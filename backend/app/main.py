from fastapi import FastAPI

from app.middleware.cors import add_cors_middleware
from app.middleware.error_handler import add_error_handlers
from app.middleware.request_logger import add_request_logger

# Import all routers
from app.api.root import router as root_router
from app.api.auth.otp import router as auth_router
from app.api.farmer.profile import router as farmer_profile_router
from app.api.farmer.cultivation import router as farmer_cultivation_router, public_router as farmer_cultivation_public_router
from app.api.farmer.dashboard import router as farmer_dashboard_router
from app.api.farmer.bookings import router as farmer_bookings_router
from app.api.farmer.bank_details import router as bank_details_router
from app.api.farmer.msp import router as msp_router
from app.api.farmer.crops import router as farmer_crops_router
from app.api.centres.centres import router as centres_router
from app.api.slots.slots import router as slots_router
from app.api.bookings.bookings import router as bookings_router
from app.api.queue.queue import router as queue_router
from app.api.procurement.procurement import router as procurement_router
from app.api.payments.payments import router as payments_router
from app.api.notifications.notifications import router as notifications_router
from app.api.ml import router as ml_router
from app.api.admin import router as admin_router
from app.api.admin.crops import router as admin_crops_router
from app.api.admin.centres import router as admin_centres_router
from app.api.admin.slots import router as admin_slots_router
from app.api.admin.reviews import router as admin_reviews_router
from app.api.admin.queue import router as admin_queue_router
from app.api.admin.procurement import router as admin_procurement_router
from app.api.admin.bank_payments import router as admin_bank_payments_router
from app.api.admin.reports import router as admin_reports_router

app = FastAPI(
    title="Farmer Procurement Platform",
    description="APIs for farmer procurement, bookings, queue, and payments.",
)

add_request_logger(app)
add_cors_middleware(app)
add_error_handlers(app)

# Include root and health routers
app.include_router(root_router)

# Include authentication router
app.include_router(auth_router)

# Include farmer routers
app.include_router(farmer_profile_router)
app.include_router(farmer_cultivation_router)
app.include_router(farmer_cultivation_public_router)
app.include_router(farmer_dashboard_router)
app.include_router(farmer_bookings_router)
app.include_router(bank_details_router)
app.include_router(msp_router)
app.include_router(farmer_crops_router)

# Include centre routers (includes nearby, slots, and detail endpoints)
app.include_router(centres_router)

# Include slots router
app.include_router(slots_router)

# Include bookings router
app.include_router(bookings_router)

# Include queue router
app.include_router(queue_router)

# Include procurement router
app.include_router(procurement_router)

# Include payments router
app.include_router(payments_router)

# Include notifications router
app.include_router(notifications_router)

# Include ML prediction router
app.include_router(ml_router)

# Include admin routers
app.include_router(admin_router)
app.include_router(admin_crops_router)
app.include_router(admin_centres_router)
app.include_router(admin_slots_router)
app.include_router(admin_reviews_router)
app.include_router(admin_queue_router)
app.include_router(admin_procurement_router)
app.include_router(admin_bank_payments_router)
app.include_router(admin_reports_router)


