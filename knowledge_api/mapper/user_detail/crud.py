from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, func, and_, or_, desc
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination import Page

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import (
    UserDetail, UserDetailCreate, UserDetailUpdate, 
    UserDetailFilter, UserDetailResponse, UserDetailStatistics
)


class UserDetailCRUD(BaseCRUD[UserDetail, UserDetailCreate, UserDetailUpdate, UserDetailFilter, UserDetailResponse, int]):
    """User details CRUD operation class"""

    def __init__(self, db: Session):
        """Initialize user details CRUD operation"""
        super().__init__(db, UserDetail)

    async def create(self, *, obj_in: UserDetailCreate, creator_id: Optional[int] = None) -> UserDetail:
        """Create user details (override base class method, add creator_id information)"""
        # Gets the creation data, using the default value of 0 if no creator_id is passed in (for system creation)
        create_data = obj_in.dict()
        if creator_id is not None:
            create_data["creator_id"] = creator_id
            create_data["updater_id"] = creator_id
        else:
            # Set the default value of 0 to represent system creation
            create_data["creator_id"] = 0
            create_data["updater_id"] = 0
            
        db_user_detail = UserDetail(**create_data)
        self.db.add(db_user_detail)
        self.db.commit()
        self.db.refresh(db_user_detail)
        return db_user_detail

    async def get_by_user_id(self, *, user_id: int) -> Optional[UserDetail]:
        """Get user details based on user ID"""
        statement = select(self.model).where(self.model.user_id == user_id)
        return self.db.exec(statement).first()

    async def update(self, *, id: int, obj_in: UserDetailUpdate, updater_id: Optional[int] = None) -> Optional[UserDetail]:
        """Update user details (override base class method, add updater_id information)"""
        db_user_detail = await self.get_by_id(id=id)
        if not db_user_detail:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        if updater_id is not None:
            update_data["updater_id"] = updater_id

        for key, value in update_data.items():
            setattr(db_user_detail, key, value)

        # update time
        db_user_detail.update_time = datetime.now()

        self.db.add(db_user_detail)
        self.db.commit()
        self.db.refresh(db_user_detail)
        return db_user_detail

    async def update_by_user_id(self, *, user_id: int, obj_in: UserDetailUpdate, updater_id: Optional[int] = None) -> Optional[UserDetail]:
        """Update user details based on user ID"""
        db_user_detail = await self.get_by_user_id(user_id=user_id)
        if not db_user_detail:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        if updater_id is not None:
            update_data["updater_id"] = updater_id

        for key, value in update_data.items():
            setattr(db_user_detail, key, value)

        # update time
        db_user_detail.update_time = datetime.now()

        self.db.add(db_user_detail)
        self.db.commit()
        self.db.refresh(db_user_detail)
        return db_user_detail

    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply filter conditions to queries (override base class methods)"""
        if filter_data.get("user_id") is not None:
            query = query.where(self.model.user_id == filter_data["user_id"])
        
        if filter_data.get("min_total_points") is not None:
            query = query.where(self.model.total_points >= filter_data["min_total_points"])
        
        if filter_data.get("max_total_points") is not None:
            query = query.where(self.model.total_points <= filter_data["max_total_points"])
        
        if filter_data.get("min_login_count") is not None:
            query = query.where(self.model.total_login_count >= filter_data["min_login_count"])
        
        if filter_data.get("min_challenge_count") is not None:
            query = query.where(self.model.total_ai_challenge_count >= filter_data["min_challenge_count"])
        
        if filter_data.get("start_time") is not None:
            query = query.where(self.model.create_time >= filter_data["start_time"])
        
        if filter_data.get("end_time") is not None:
            query = query.where(self.model.create_time <= filter_data["end_time"])

        return query

    async def get_user_detail_with_rates(self, *, user_id: int) -> Optional[UserDetailResponse]:
        """Acquire user details and calculate metrics such as success rates"""
        user_detail = await self.get_by_user_id(user_id=user_id)
        if not user_detail:
            return None

        # Calculate the challenge success rate
        challenge_success_rate = None
        if user_detail.total_ai_challenge_count > 0:
            challenge_success_rate = round(
                (user_detail.total_ai_challenge_success_count / user_detail.total_ai_challenge_count) * 100, 2
            )

        # Calculate point usage
        points_usage_rate = None
        if user_detail.total_points_earned > 0:
            points_usage_rate = round(
                (user_detail.total_points_spent / user_detail.total_points_earned) * 100, 2
            )

        # Constructing response data
        response_data = user_detail.dict()
        response_data["challenge_success_rate"] = challenge_success_rate
        response_data["points_usage_rate"] = points_usage_rate

        return UserDetailResponse(**response_data)

    async def update_login_count(self, *, user_id: int) -> bool:
        """Update user logins and last active time"""
        user_detail = await self.get_by_user_id(user_id=user_id)
        if not user_detail:
            # If the user details do not exist, create a new record
            await self.create(obj_in=UserDetailCreate(
                user_id=user_id,
                total_login_count=1,
                last_active_time=datetime.now()
            ), creator_id=0)  # System creation
            return True

        # Update existing records
        user_detail.total_login_count += 1
        user_detail.last_active_time = datetime.now()
        user_detail.update_time = datetime.now()

        self.db.add(user_detail)
        self.db.commit()
        return True

    async def update_challenge_stats(self, *, user_id: int, success: bool = False) -> bool:
        """Update user challenge statistics"""
        user_detail = await self.get_by_user_id(user_id=user_id)
        if not user_detail:
            # If the user details do not exist, create a new record
            await self.create(obj_in=UserDetailCreate(
                user_id=user_id,
                total_ai_challenge_count=1,
                total_ai_challenge_success_count=1 if success else 0
            ), creator_id=0)  # System creation
            return True

        # Update existing records
        user_detail.total_ai_challenge_count += 1
        if success:
            user_detail.total_ai_challenge_success_count += 1
        user_detail.last_active_time = datetime.now()
        user_detail.update_time = datetime.now()

        self.db.add(user_detail)
        self.db.commit()
        return True

    async def update_points(self, *, user_id: int, points_change: int, is_earned: bool = True) -> bool:
        """Update user points"""
        user_detail = await self.get_by_user_id(user_id=user_id)
        if not user_detail:
            # If the user details do not exist, create a new record
            if is_earned and points_change > 0:
                await self.create(obj_in=UserDetailCreate(
                    user_id=user_id,
                    total_points=points_change,
                    available_points=points_change,
                    total_points_earned=points_change
                ), creator_id=0)  # System creation
            return True

        # Update existing records
        if is_earned:
            # Earn points
            user_detail.total_points += points_change
            user_detail.available_points += points_change
            user_detail.total_points_earned += points_change
        else:
            # consumption points
            if user_detail.available_points >= points_change:
                user_detail.available_points -= points_change
                user_detail.total_points_spent += points_change
            else:
                return False  # Insufficient points

        user_detail.last_active_time = datetime.now()
        user_detail.update_time = datetime.now()

        self.db.add(user_detail)
        self.db.commit()
        return True

    async def update_card_count(self, *, user_id: int, count_change: int) -> bool:
        """Update the number of user cards"""
        user_detail = await self.get_by_user_id(user_id=user_id)
        if not user_detail:
            # If the user details do not exist, create a new record
            if count_change > 0:
                await self.create(obj_in=UserDetailCreate(
                    user_id=user_id,
                    total_card_count=count_change
                ), creator_id=0)  # System creation
            return True

        # Update existing records
        user_detail.total_card_count += count_change
        user_detail.last_active_time = datetime.now()
        user_detail.update_time = datetime.now()

        self.db.add(user_detail)
        self.db.commit()
        return True

    async def update_blind_box_count(self, *, user_id: int) -> bool:
        """Update the number of times the user opens the blind box"""
        user_detail = await self.get_by_user_id(user_id=user_id)
        if not user_detail:
            # If the user details do not exist, create a new record
            await self.create(obj_in=UserDetailCreate(
                user_id=user_id,
                total_blind_box_opened=1
            ), creator_id=0)  # System creation
            return True

        # Update existing records
        user_detail.total_blind_box_opened += 1
        user_detail.last_active_time = datetime.now()
        user_detail.update_time = datetime.now()

        self.db.add(user_detail)
        self.db.commit()
        return True

    async def get_top_users_by_points(self, *, limit: int = 10) -> List[UserDetail]:
        """Get the top N users in the points leaderboard"""
        statement = select(self.model).order_by(desc(self.model.total_points)).limit(limit)
        return self.db.exec(statement).all()

    async def get_top_users_by_challenges(self, *, limit: int = 10) -> List[UserDetail]:
        """Get the top N users in the challenge list"""
        statement = select(self.model).order_by(desc(self.model.total_ai_challenge_count)).limit(limit)
        return self.db.exec(statement).all()

    async def get_most_active_users(self, *, limit: int = 10) -> List[UserDetail]:
        """Get the most active users (sorted by login count)"""
        statement = select(self.model).order_by(desc(self.model.total_login_count)).limit(limit)
        return self.db.exec(statement).all()

    async def get_statistics(self) -> UserDetailStatistics:
        """Get user details statistics"""
        # total users
        total_users_result = self.db.exec(select(func.count(self.model.id))).one()
        
        # total system integral
        total_points_result = self.db.exec(select(func.sum(self.model.total_points))).one()
        total_points = total_points_result or 0
        
        # user average points
        avg_points_result = self.db.exec(select(func.avg(self.model.total_points))).one()
        avg_points = float(avg_points_result or 0)
        
        # total number of challenges
        total_challenges_result = self.db.exec(select(func.sum(self.model.total_ai_challenge_count))).one()
        total_challenges = total_challenges_result or 0
        
        # Total number of successful challenges
        total_success_challenges_result = self.db.exec(select(func.sum(self.model.total_ai_challenge_success_count))).one()
        total_success_challenges = total_success_challenges_result or 0
        
        # average challenge success rate
        avg_success_rate = 0.0
        if total_challenges > 0:
            avg_success_rate = (total_success_challenges / total_challenges) * 100
        
        # Total number of cards in the system
        total_cards_result = self.db.exec(select(func.sum(self.model.total_card_count))).one()
        total_cards = total_cards_result or 0
        
        # Total blind box openings
        total_blind_boxes_result = self.db.exec(select(func.sum(self.model.total_blind_box_opened))).one()
        total_blind_boxes = total_blind_boxes_result or 0
        
        # The most active user (simplified version, only returns the user ID)
        most_active = await self.get_most_active_users(limit=5)
        most_active_list = [{"user_id": user.user_id, "login_count": user.total_login_count} for user in most_active]

        return UserDetailStatistics(
            total_users=total_users_result,
            total_points_in_system=total_points,
            average_points_per_user=round(avg_points, 2),
            total_challenges=total_challenges,
            average_challenge_success_rate=round(avg_success_rate, 2),
            total_cards_in_system=total_cards,
            total_blind_boxes_opened=total_blind_boxes,
            most_active_users=most_active_list
        ) 