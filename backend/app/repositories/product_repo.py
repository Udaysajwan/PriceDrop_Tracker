import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from backend.app.database_firebase import get_firestore_db


class ProductRepository:
    def __init__(self):
        pass

    @property
    def collection(self):
        return get_firestore_db().collection("products")

    def alerts_collection(self, user_id: Optional[str] = None):
        if user_id is not None:
            return get_firestore_db().collection("users").document(str(user_id)).collection("alerts")
        return get_firestore_db().collection("alerts")

    def create_alert(
        self,
        product_id: str,
        user_id: str,
        product_title: str,
        product_url: str,
        target_price: float,
        current_price: float,
        currency: str = "INR",
        source: str = "price_check",
        status: str = "active",
    ) -> Dict[str, Any]:
        product = self.get_by_id(product_id, user_id=user_id)
        if not product:
            raise ValueError("Product not found for this user")

        existing = self.get_active_alert_for_product(product_id, user_id=user_id)
        if existing:
            return existing

        alert_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        alert_data = {
            "id": alert_id,
            "product_id": str(product_id),
            "user_id": str(user_id),
            "product_title": product_title,
            "product_url": product_url,
            "target_price": float(target_price),
            "current_price": float(current_price),
            "currency": currency or "INR",
            "source": source,
            "status": status,
            "created_at": created_at,
            "updated_at": created_at,
        }
        self.alerts_collection(user_id).document(alert_id).set(alert_data)
        return alert_data

    def get_active_alert_for_product(self, product_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if user_id is None:
            product = self.get_by_id(product_id)
            if not product:
                return None
            user_id = product.get("user_id")

        alerts = self.alerts_collection(user_id).where("product_id", "==", str(product_id)).where("status", "==", "active").stream()
        if not alerts:
            return None
        first = alerts[0].to_dict()
        first["id"] = alerts[0].id
        return first

    def list_alerts_for_product(self, product_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if user_id is None:
            product = self.get_by_id(product_id)
            if not product:
                return []
            user_id = product.get("user_id")

        alerts = self.alerts_collection(user_id).where("product_id", "==", str(product_id)).stream()
        results = []
        for doc in alerts:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def resolve_active_alert(self, product_id: str, user_id: Optional[str] = None, current_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        active = self.get_active_alert_for_product(product_id, user_id=user_id)
        if not active:
            return None

        if user_id is None:
            product = self.get_by_id(product_id)
            if not product:
                return None
            user_id = product.get("user_id")

        alert_id = active["id"]
        updated_at = datetime.now(timezone.utc).isoformat()
        updates = {
            "status": "resolved",
            "updated_at": updated_at,
        }
        if current_price is not None:
            updates["current_price"] = float(current_price)

        self.alerts_collection(user_id).document(alert_id).update(updates)
        resolved = self.alerts_collection(user_id).document(alert_id).get().to_dict()
        resolved["id"] = alert_id
        return resolved

    def get_alerts_for_user(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        alerts = self.alerts_collection(user_id).stream()
        results = []
        for doc in alerts:
            data = doc.to_dict()
            if status is not None and data.get("status") != status:
                continue
            data["id"] = doc.id
            results.append(data)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def get_alert_by_id(self, alert_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if user_id is None:
            return None
        doc = self.alerts_collection(user_id).document(str(alert_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    def update_alert_status(self, alert_id: str, user_id: str, status: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.alerts_collection(user_id).document(str(alert_id))
        if not doc_ref.get().exists:
            return None
        doc_ref.update({
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        updated = doc_ref.get().to_dict()
        updated["id"] = doc_ref.id
        return updated

    def create(
        self,
        user_id: str,
        title: str,
        url: str,
        target_price: float,
        current_price: float,
        currency: str = "INR",
        image_url: Optional[str] = None,
        in_stock: bool = True
    ) -> Dict[str, Any]:
        product_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        product_data = {
            "id": product_id,
            "user_id": str(user_id),
            "title": title,
            "url": str(url),
            "target_price": float(target_price),
            "current_price": float(current_price),
            "currency": currency or "USD",
            "image_url": image_url,
            "in_stock": in_stock,
            "last_scraped_at": now_str,
            "created_at": now_str,
            "updated_at": now_str,
        }
        self.collection.document(product_id).set(product_data)

        # Create initial history document in subcollection
        self.add_price_history(product_id, current_price, now_str)

        return product_data

    def list_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        docs = self.collection.where("user_id", "==", str(user_id)).stream()
        results = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            results.append(data)
        # Sort descending by created_at
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def get_by_id(self, product_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        doc = self.collection.document(str(product_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["id"] = doc.id
        if user_id is not None and str(data.get("user_id")) != str(user_id):
            return None
        return data

    def update(self, product_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(str(product_id))
        doc = doc_ref.get()
        if not doc.exists:
            return None
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        doc_ref.update(updates)
        updated_data = doc_ref.get().to_dict()
        updated_data["id"] = doc_ref.id
        return updated_data

    def delete(self, product_id: str) -> bool:
        doc_ref = self.collection.document(str(product_id))
        doc = doc_ref.get()
        if not doc.exists:
            return False
        # In Firestore, deleting a document reference removes the document
        doc_ref.delete()
        return True

    def add_price_history(self, product_id: str, price: float, scraped_at: Optional[str] = None) -> Dict[str, Any]:
        if not scraped_at:
            scraped_at = datetime.now(timezone.utc).isoformat()

        hist_id = str(uuid.uuid4())
        hist_data = {
            "id": hist_id,
            "product_id": str(product_id),
            "price": float(price),
            "scraped_at": scraped_at,
        }

        # Subcollection: products/{product_id}/history/{hist_id}
        doc_ref = self.collection.document(str(product_id))
        doc_ref.collection("history").document(hist_id).set(hist_data)

        # Update product current_price and last_scraped_at
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({
                "current_price": float(price),
                "last_scraped_at": scraped_at,
                "updated_at": scraped_at
            })

        return hist_data

    def get_price_history(self, product_id: str) -> List[Dict[str, Any]]:
        doc_ref = self.collection.document(str(product_id))
        history_docs = doc_ref.collection("history").stream()
        results = []
        for d in history_docs:
            data = d.to_dict()
            data["id"] = d.id
            results.append(data)
        results.sort(key=lambda x: x.get("scraped_at", ""))
        return results

    def get_summary(self, product_id: str) -> Optional[Dict[str, Any]]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        history = self.get_price_history(product_id)
        target_price = float(product.get("target_price", 0.0))
        current_price = float(product.get("current_price")) if product.get("current_price") is not None else None

        if not history:
            return {
                "product_id": product_id,
                "title": product.get("title", ""),
                "target_price": target_price,
                "current_price": current_price,
                "lowest_price": current_price,
                "highest_price": current_price,
                "average_price": current_price,
                "total_checks": 0,
                "price_dropped": False,
                "savings_amount": 0.0,
                "savings_percent": 0.0,
                "first_recorded_price": current_price,
                "percent_change_overall": 0.0
            }

        prices = [h["price"] for h in history]
        lowest = min(prices)
        highest = max(prices)
        average = round(sum(prices) / len(prices), 2)
        first_price = history[0]["price"]
        current = current_price if current_price is not None else prices[-1]

        price_dropped = current <= target_price
        savings_amount = round(target_price - current, 2) if price_dropped else 0.0
        savings_percent = round((savings_amount / target_price) * 100, 2) if (price_dropped and target_price > 0) else 0.0

        percent_change_overall = None
        if first_price > 0:
            percent_change_overall = round(((current - first_price) / first_price) * 100, 2)

        return {
            "product_id": product_id,
            "title": product.get("title", ""),
            "target_price": target_price,
            "current_price": current,
            "lowest_price": lowest,
            "highest_price": highest,
            "average_price": average,
            "total_checks": len(history),
            "price_dropped": price_dropped,
            "savings_amount": savings_amount,
            "savings_percent": savings_percent,
            "first_recorded_price": first_price,
            "percent_change_overall": percent_change_overall
        }

    def get_all_active_products(self) -> List[Dict[str, Any]]:
        docs = self.collection.stream()
        results = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            results.append(data)
        return results


product_repo = ProductRepository()
