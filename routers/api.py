from fastapi import APIRouter
from routers.v1.exam_router import exam_router
from routers.v1.user_router import user_router

router = APIRouter(
    prefix='/api/v1'
)

router.include_router(user_router)
router.include_router(exam_router)