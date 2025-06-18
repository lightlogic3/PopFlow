from fastapi import APIRouter

from card_game.api.card_challenge_api import challenge_router
from card_game.api.card_reward_api import reward_router
from card_game.api.card_series_api import router_card_game_series
from card_game.api.card_api import router_card_game
from card_game.api.card_unlock_api import router_card_unlock
from card_game.api.user_point_api import router_user_point


card_game = APIRouter(prefix="/api/card_game")

# register route
card_game.include_router(router_card_game_series)
card_game.include_router(router_card_game)
card_game.include_router(router_card_unlock)
card_game.include_router(router_user_point)
card_game.include_router(challenge_router)

card_game.include_router(reward_router)


