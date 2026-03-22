from .common         import router as common_router
from .catalog        import router as catalog_router
from .cart           import router as cart_router
from .orders         import router as orders_router
from .size           import router as size_router
from .referral       import router as referral_router
from .qc             import router as qc_router
from .wishlist       import router as wishlist_router
from .notifications  import router as notifications_router
from .addresses      import router as addresses_router
from .price_adjust   import router as price_adjust_router
from .admin_products import router as admin_products_router
from .admin_orders   import router as admin_orders_router
from .admin_qc       import router as admin_qc_router
from .admin_misc     import router as admin_misc_router
from .support        import router as support_router  # MUST be last

all_routers = [
    common_router,
    catalog_router,
    cart_router,
    orders_router,
    size_router,
    referral_router,
    qc_router,
    wishlist_router,
    notifications_router,
    addresses_router,
    price_adjust_router,
    admin_products_router,
    admin_orders_router,
    admin_qc_router,
    admin_misc_router,
    support_router,  # LAST — catches all remaining admin text
]
