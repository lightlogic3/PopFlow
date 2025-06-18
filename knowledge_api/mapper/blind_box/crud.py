"""Blind box CRUD operation"""
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_, or_
from fastapi_pagination import Page
from sqlmodel import text
from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.blind_box.base import (
    BlindBox, 
    BlindBoxCreate, 
    BlindBoxUpdate, 
    BlindBoxFilter, 
    BlindBoxResponse,
    BlindBoxCard,
    BlindBoxCardCreate,
    BlindBoxCardUpdate,
    BlindBoxCardResponse
)
from knowledge_api.mapper.card.base import CardAlg, Card


class BlindBoxCRUD(BaseCRUD[BlindBox, BlindBoxCreate, BlindBoxUpdate, BlindBoxFilter, BlindBoxResponse, int]):
    """Blind box CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation"""
        super().__init__(db, BlindBox)
    
    async def create(self, obj_in: BlindBoxCreate, creator_id: Optional[int] = None) -> BlindBox:
        """Create a blind box

Args:
obj_in: Creating Data
creator_id: Creator ID

Returns:
BlindBox: Created blind box"""
        return await super().create(obj_in, creator_id=creator_id, updater_id=creator_id)
    
    async def update(self, id: int, obj_in: BlindBoxUpdate, updater_id: Optional[int] = None) -> Optional[BlindBox]:
        """Update blind box

Args:
ID: Blind box ID
obj_in: Update Data
updater_id: Updater ID

Returns:
Optional [BlindBox]: updated blind box"""
        # Get the current record
        db_obj = await self.get_by_id(id=id)
        if db_obj is None or db_obj.is_deleted == 1:
            return None
            
        # Get updated data
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Add Updater ID
        if updater_id is not None:
            update_data["updater_id"] = updater_id
        
        # Update object properties
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        
        # commit changes
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, id: int) -> Optional[BlindBox]:
        """Get blind box by ID (exclude deleted)

Args:
ID: Blind box ID

Returns:
Optional [BlindBox]: Blind Box or None"""
        statement = select(self.model).where(
            and_(self.model.id == id, self.model.is_deleted == 0)
        )
        result = self.db.exec(statement).first()
        return result
    
    async def get_active_blind_boxes(self, skip: int = 0, limit: int = 100) -> List[BlindBox]:
        """Get a list of enabled blind boxes

Args:
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [BlindBox]: List of blind boxes"""
        statement = select(self.model).where(
            and_(self.model.status == 1, self.model.is_deleted == 0)
        ).order_by(self.model.create_time.desc()).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
    
    async def soft_delete(self, id: int, updater_id: Optional[int] = None) -> bool:
        """soft delete blind box

Args:
ID: Blind box ID
updater_id: Updater ID

Returns:
Bool: whether the deletion was successful"""
        db_obj = await self.get_by_id(id=id)
        if db_obj is None:
            return False
            
        db_obj.is_deleted = 1
        if updater_id is not None:
            db_obj.updater_id = updater_id
            
        self.db.add(db_obj)
        self.db.commit()
        return True
    
    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply Filter Criteria to Queries

Args:
Query: SQLModel query object
filter_data: Filter Dictionary

Returns:
Query objects to which filter criteria have been applied"""
        # By default, only undeleted records are queried.
        query = query.where(self.model.is_deleted == 0)
        
        for field, value in filter_data.items():
            if value is not None and hasattr(self.model, field):
                if field == "name":
                    # Name support fuzzy query
                    query = query.where(self.model.name.like(f"%{value}%"))
                else:
                    # Other fields match exactly
                    query = query.where(getattr(self.model, field) == value)
        
        return query

    async def get_blind_box_cards(self, blind_box_id: int) -> List[CardAlg]:
        """Obtain all cards of the specified blind box

Args:
blind_box_id: blind box ID

Returns:
List [CardAlg]: List of blind box cards (converted to the object format required by the algorithm)"""
        # Define unlock_type string to integer mapping
        unlock_type_map = {
            "points": 1,  # Points unlocked
            "blind_box": 2,  # Blind box unlock
            "both": 3,  # Either way is fine.
            "box_only": 4,  # Only the blind box can be unlocked.
            "event": 5,  # activity acquisition
            "admin": 6,  # administrator issued
        }

        # Joint query blind box card association table and card table
        query = text("""
                     SELECT c.id,
                            c.name,
                            c.rarity,
                            c.description,
                            c.image_url,
                            c.unlock_type,
                            c.points_required,
                            c.duplicate_points,
                            c.is_limited,
                            c.limited_count,
                            bbc.probability,
                            bbc.weight,
                            bbc.is_special_reward
                     FROM blind_box_card bbc
                              JOIN card c ON bbc.card_id = c.id
                     WHERE bbc.blind_box_id = :blind_box_id
                       AND c.status = 1
                       AND c.is_deleted = 0
                     """)

        results = self.db.exec(query.bindparams(
            blind_box_id=blind_box_id
        )).all()
        # Convert query results to a list of CardAlg objects
        cards = []
        for row in results:
            # Mapping string unlock_type to integers
            unlock_type_int = unlock_type_map.get(row.unlock_type, 0)  # Default is 0
            
            card = CardAlg(
                id=row.id,
                name=row.name,
                rarity=row.rarity,
                description=row.description,
                image_url=row.image_url,
                unlock_type=unlock_type_int,  # Use the mapped integer value
                points_required=row.points_required,
                duplicate_points=row.duplicate_points,
                is_limited=bool(row.is_limited),
                limited_count=row.limited_count,
                probability=row.probability,
                weight=row.weight,
                is_special_reward=bool(row.is_special_reward)
            )
            cards.append(card)

        return cards


class BlindBoxCardCRUD(BaseCRUD[BlindBoxCard, BlindBoxCardCreate, BlindBoxCardUpdate, Dict, BlindBoxCardResponse, int]):
    """Blind Box Card Association CRUD Operation Class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation"""
        super().__init__(db, BlindBoxCard)
    
    async def create(self, obj_in: BlindBoxCardCreate, creator_id: Optional[int] = None) -> BlindBoxCard:
        """Create a blind box card association

Args:
obj_in: Creating Data
creator_id: Creator ID

Returns:
BlindBoxCard: created association record"""
        return await super().create(obj_in, creator_id=creator_id, updater_id=creator_id)
    
    async def get_cards_by_blind_box(self, blind_box_id: int) -> List[BlindBoxCard]:
        """Get the associated card list according to the blind box ID

Args:
blind_box_id: blind box ID

Returns:
List [BlindBoxCard]: List of associated cards"""
        statement = select(self.model).where(self.model.blind_box_id == blind_box_id)
        results = self.db.exec(statement).all()
        return results
    
    async def delete_by_blind_box_and_card(self, blind_box_id: int, card_id: int) -> bool:
        """Delete the association between the specified blind box and the card

Args:
blind_box_id: blind box ID
card_id: Card ID

Returns:
Bool: whether the deletion was successful"""
        statement = select(self.model).where(
            and_(self.model.blind_box_id == blind_box_id, self.model.card_id == card_id)
        )
        result = self.db.exec(statement).first()
        
        if result:
            self.db.delete(result)
            self.db.commit()
            return True
        return False
    
    async def batch_create_cards(self, blind_box_id: int, card_configs: List[Dict], creator_id: Optional[int] = None) -> List[BlindBoxCard]:
        """Batch creation of blind box card associations

Args:
blind_box_id: blind box ID
card_configs: Card Configuration List
creator_id: Creator ID

Returns:
List [BlindBoxCard]: List of associated records created"""
        results = []
        for config in card_configs:
            card_create = BlindBoxCardCreate(
                blind_box_id=blind_box_id,
                card_id=config["card_id"],
                probability=config["probability"],
                weight=config.get("weight", 100),
                is_special_reward=config.get("is_special_reward", 0)
            )
            result = await self.create(card_create, creator_id)
            results.append(result)
        
        return results
    
    async def clear_blind_box_cards(self, blind_box_id: int) -> bool:
        """Empty all card associations of the specified blind box

Args:
blind_box_id: blind box ID

Returns:
Bool: was the clearance successful?"""
        statement = select(self.model).where(self.model.blind_box_id == blind_box_id)
        results = self.db.exec(statement).all()
        
        for result in results:
            self.db.delete(result)
        
        self.db.commit()
        return True

    async def get_card_binding_status(
            self,
            blind_box_id: int,
            name: Optional[str] = None,
            rarity: Optional[int] = None,
            page: int = 1,
            size: int = 12
    ) -> Dict[str, Any]:
        """Get the bound and unbound cards of the blind box

Args:
blind_box_id: blind box ID
Name: Card Name Search
Rarity: rarity filter
Page: page number
Size: Size per page

Returns:
Dict [str, Any]: Dictionary containing bound and unbound cards"""
        # 1. Get the bound card
        bound_statement = select(
            BlindBoxCard, Card
        ).join(
            Card, BlindBoxCard.card_id == Card.id
        ).where(
            BlindBoxCard.blind_box_id == blind_box_id
        )

        # app name filtering
        if name:
            bound_statement = bound_statement.where(Card.name.like(f"%{name}%"))

        # Applied Rarity Filtering
        if rarity is not None:
            bound_statement = bound_statement.where(Card.rarity == rarity)

        bound_results = self.db.exec(bound_statement).all()
        bound_card_ids = [result[1].id for result in bound_results]

        # Build Bound Card Result
        bound_cards = []
        for blind_box_card, card in bound_results:
            bound_cards.append({
                "blind_box_card_id": blind_box_card.id,
                "card_id": card.id,
                "name": card.name,
                "description": card.description,
                "image_url": card.image_url,
                "rarity": card.rarity,
                "probability": blind_box_card.probability,
                "weight": blind_box_card.weight,
                "is_special_reward": blind_box_card.is_special_reward
            })

        # 2. Get unbound cards
        unbound_statement = select(Card).where(
            and_(
                Card.status == 1,  # Get only enabled cards
                Card.is_deleted == 0,  # Get only undeleted cards
                or_(
                    Card.id.not_in(bound_card_ids) if bound_card_ids else True
                )
            )
        )

        # app name filtering
        if name:
            unbound_statement = unbound_statement.where(Card.name.like(f"%{name}%"))

        # Applied Rarity Filtering
        if rarity is not None:
            unbound_statement = unbound_statement.where(Card.rarity == rarity)

        # Calculate the total number of records
        unbound_count_statement = select(
            Card.id
        ).where(
            and_(
                Card.status == 1,
                Card.is_deleted == 0,
                or_(
                    Card.id.not_in(bound_card_ids) if bound_card_ids else True
                )
            )
        )

        # app name filtering
        if name:
            unbound_count_statement = unbound_count_statement.where(Card.name.like(f"%{name}%"))

        # Applied Rarity Filtering
        if rarity is not None:
            unbound_count_statement = unbound_count_statement.where(Card.rarity == rarity)

        unbound_total = len(self.db.exec(unbound_count_statement).all())

        # app paging
        offset = (page - 1) * size
        unbound_statement = unbound_statement.offset(offset).limit(size)

        unbound_cards = self.db.exec(unbound_statement).all()

        # Build unbound card result
        unbound_card_items = []
        for card in unbound_cards:
            unbound_card_items.append({
                "id": card.id,
                "name": card.name,
                "description": card.description,
                "image_url": card.image_url,
                "rarity": card.rarity,
            })

        return {
            "bound_cards": bound_cards,
            "unbound_cards": {
                "items": unbound_card_items,
                "total": unbound_total
            }
        }