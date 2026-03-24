# locales/translations.py
# Все тексты бота. Ключ → {ru, en, et}

T = {
    # Язык
    "choose_language":    {"ru": "🌍 Выберите язык:", "en": "🌍 Choose language:", "et": "🌍 Valige keel:"},
    "language_set":       {"ru": "✅ Язык: Русский",  "en": "✅ Language: English", "et": "✅ Keel: Eesti"},

    # Приветствие
    "welcome": {
        "ru": (
            "🏪 *3XCLUSIV3 — Одежда из Китая*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "👋 Добро пожаловать!\n\n"
            "🌐 *Хотите удобный шопинг?*\n"
            "Запустите наш веб-магазин — там удобная галерея товаров, фильтры, корзина и оформление заказа прямо в браузере!\n\n"
            "🤖 *Предпочитаете бота?*\n"
            "Всё то же самое доступно здесь — каталог, корзина, заказы, избранное и поддержка.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🛍 Одежда, обувь и аксессуары\n"
            "💵 Оплата наличными при получении\n"
            "🚚 Доставка по всей Эстонии\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Выберите раздел ниже 👇"
        ),
        "en": (
            "🏪 *3XCLUSIV3 — Clothing from China*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "👋 Welcome!\n\n"
            "🌐 *Want a better shopping experience?*\n"
            "Open our web store — browse products in a gallery, filter by category, manage your cart and place orders right in the browser!\n\n"
            "🤖 *Prefer the bot?*\n"
            "Everything is available here too — catalog, cart, orders, wishlist and support.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🛍 Clothing, shoes & accessories\n"
            "💵 Cash on delivery\n"
            "🚚 Delivery across Estonia\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Choose a section below 👇"
        ),
        "et": (
            "🏪 *3XCLUSIV3 — Rõivad Hiinast*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "👋 Tere tulemast!\n\n"
            "🌐 *Soovite mugavamat ostlemist?*\n"
            "Avage meie veebipood — vaadake tooteid galeriis, filtreerige kategooriate järgi, hallake ostukorvi ja esitage tellimusi otse brauseris!\n\n"
            "🤖 *Eelistate botti?*\n"
            "Kõik on saadaval ka siin — kataloog, ostukorv, tellimused, lemmikud ja tugi.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🛍 Rõivad, jalatsid ja aksessuaarid\n"
            "💵 Tasumine sularahas kohaletoimetamisel\n"
            "🚚 Tarne üle Eesti\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Valige allpool menüüst 👇"
        ),
    },

    # ── ВЕБ-МАГАЗИН ──────────────────────────────────────────────────────────
    "🌐 Открыть веб-магазин": {
        "ru": "🌐 Открыть веб-магазин",
        "en": "🌐 Open Web Store",
        "et": "🌐 Ava veebipood",
    },

    # ── КНОПКИ ПОЛЬЗОВАТЕЛЯ ──────────────────────────────────────────────────
    "🛍 Каталог":         {"ru": "🛍 Каталог",         "en": "🛍 Catalog",          "et": "🛍 Kataloog"},
    "🛒 Корзина":         {"ru": "🛒 Корзина",         "en": "🛒 Cart",             "et": "🛒 Ostukorv"},
    "📦 Мои заказы":     {"ru": "📦 Мои заказы",      "en": "📦 My Orders",        "et": "📦 Minu tellimused"},
    "📏 Размер":         {"ru": "📏 Подбор размера",   "en": "📏 Size Guide",       "et": "📏 Suuruse soovitus"},
    "🔗 Рефералы":       {"ru": "🔗 Пригласить друзей","en": "🔗 Invite Friends",   "et": "🔗 Kutsu sõpru"},
    "💬 Продавец":       {"ru": "💬 Написать продавцу","en": "💬 Contact seller",   "et": "💬 Kirjuta müüjale"},
    "⚙️ Настройки":     {"ru": "⚙️ Настройки",       "en": "⚙️ Settings",        "et": "⚙️ Seaded"},
    "🏠 Главное меню":   {"ru": "🏠 Главное меню",    "en": "🏠 Main Menu",        "et": "🏠 Peamenüü"},
    "❌ Отмена":          {"ru": "❌ Отмена",           "en": "❌ Cancel",           "et": "❌ Tühista"},
    "☰ Ещё":             {"ru": "☰ Ещё",              "en": "☰ More",             "et": "☰ Rohkem"},
    "🔙 Назад":           {"ru": "🔙 Назад",            "en": "🔙 Back",             "et": "🔙 Tagasi"},

    "❤️ Избранное":      {"ru": "❤️ Избранное",       "en": "❤️ Wishlist",         "et": "❤️ Lemmikud"},
    "🔔 Уведомления":    {"ru": "🔔 Уведомления",     "en": "🔔 Notifications",     "et": "🔔 Teavitused"},
    "📍 Адреса":         {"ru": "📍 Адреса",           "en": "📍 Addresses",         "et": "📍 Aadressid"},

    # ── КНОПКИ АДМИНА ────────────────────────────────────────────────────────
    "📦 Товары":         {"ru": "📦 Товары",           "en": "📦 Products",         "et": "📦 Tooted"},
    "📋 Заказы":         {"ru": "📋 Заказы",           "en": "📋 Orders",           "et": "📋 Tellimused"},
    "📸 QC":             {"ru": "📸 Отправить QC",     "en": "📸 Send QC",          "et": "📸 Saada QC"},
    "⭐ Отзывы":         {"ru": "⭐ Отзывы",           "en": "⭐ Reviews",          "et": "⭐ Arvustused"},
    "🔗 Рефералы адм":  {"ru": "🔗 Рефералы",         "en": "🔗 Referrals",        "et": "🔗 Suunamised"},
    "📊 Статистика":     {"ru": "📊 Статистика",       "en": "📊 Statistics",       "et": "📊 Statistika"},
    "📈 Товары стат":    {"ru": "📈 Статистика товаров", "en": "📈 Product stats",   "et": "📈 Toodete statistika"},
    "🚚 Доставка":       {"ru": "🚚 Доставка",        "en": "🚚 Delivery zones",   "et": "🚚 Tarnepiirkonnad"},
    "📣 Рассылка":       {"ru": "📣 Рассылка",         "en": "📣 Broadcast",        "et": "📣 Teavitus"},

    # ── КАТАЛОГ ──────────────────────────────────────────────────────────────
    "choose_category":   {"ru": "👇 Выберите категорию:", "en": "👇 Choose category:", "et": "👇 Vali kategooria:"},
    "👕 Одежда":         {"ru": "👕 Одежда",    "en": "👕 Clothes",    "et": "👕 Riided"},
    "👟 Обувь":          {"ru": "👟 Обувь",     "en": "👟 Shoes",      "et": "👟 Jalatsid"},
    "👜 Аксессуары":    {"ru": "👜 Аксессуары","en": "👜 Accessories","et": "👜 Aksessuaarid"},
    "no_products":       {"ru": "❌ Нет товаров в этой категории.", "en": "❌ No products.", "et": "❌ Tooteid pole."},
    "⬅️ Назад":         {"ru": "⬅️ Назад",    "en": "⬅️ Back",      "et": "⬅️ Tagasi"},
    "🛒 В корзину":     {"ru": "🛒 В корзину", "en": "🛒 Add to cart","et": "🛒 Lisa korvi"},
    "added_to_cart":     {"ru": "✅ *{name}* добавлен в корзину!", "en": "✅ *{name}* added!", "et": "✅ *{name}* lisatud!"},

    # ── КОРЗИНА ──────────────────────────────────────────────────────────────
    "cart_empty":        {"ru": "🛒 Корзина пуста. Перейдите в каталог!", "en": "🛒 Cart is empty!", "et": "🛒 Ostukorv on tühi!"},
    "cart_header":       {"ru": "🛒 *Ваша корзина:*\n\n", "en": "🛒 *Your cart:*\n\n", "et": "🛒 *Teie ostukorv:*\n\n"},
    "cart_total":        {"ru": "\n💰 *Итого: {total} €*", "en": "\n💰 *Total: {total} €*", "et": "\n💰 *Kokku: {total} €*"},
    "cart_cleared":      {"ru": "🗑 Корзина очищена.", "en": "🗑 Cart cleared.", "et": "🗑 Ostukorv tühjendatud."},
    "✅ Оформить":       {"ru": "✅ Оформить заказ", "en": "✅ Checkout",    "et": "✅ Vormista tellimus"},
    "🗑 Очистить":       {"ru": "🗑 Очистить корзину","en": "🗑 Clear Cart", "et": "🗑 Tühjenda korv"},

    # ── ОФОРМЛЕНИЕ ЗАКАЗА ─────────────────────────────────────────────────────
    "enter_name":        {"ru": "👤 Введите *имя и фамилию* (например: Иван Иванов):", "en": "👤 Enter your *first and last name* (e.g. John Smith):", "et": "👤 Sisestage *ees- ja perekonnanimi* (nt Jaan Tamm):"},
    "invalid_name":      {"ru": "❌ Введите *имя и фамилию* — только буквы, минимум 2 слова.", "en": "❌ Enter *first and last name* — letters only, at least 2 words.", "et": "❌ Sisestage *ees- ja perekonnanimi* — ainult tähed, vähemalt 2 sõna."},
    "enter_username":     {"ru": "📱 Введите ваш *username* в Telegram (без @, например: ivan123):", "en": "📱 Enter your Telegram *username* (without @, e.g. john123):", "et": "📱 Sisestage oma Telegrami *kasutajanimi* (ilma @, nt jaan123):"},
    "invalid_username":   {"ru": "❌ Неверный username. Только латиница, цифры и _ . От 5 до 32 символов.", "en": "❌ Invalid username. Only letters, digits and _ . 5–32 characters.", "et": "❌ Vale kasutajanimi. Ainult ladina tähed, numbrid ja _ . 5–32 tähemärki."},
    "enter_phone":       {"ru": "📞 Введите эстонский *номер телефона* (8 цифр, например: 56781234):", "en": "📞 Enter Estonian *phone number* (8 digits, e.g. 56781234):", "et": "📞 Sisestage Eesti *telefoninumber* (8 numbrit, nt 56781234):"},
    "invalid_phone":     {"ru": "❌ Неверный номер. Введите эстонский номер: 8 цифр (например: 56781234).", "en": "❌ Invalid number. Enter Estonian phone: 8 digits (e.g. 56781234).", "et": "❌ Vale number. Sisestage Eesti number: 8 numbrit (nt 56781234)."},
    "enter_address":     {"ru": "📍 Введите *район* для встречи с продавцом:", "en": "📍 Enter meeting *area*:", "et": "📍 Sisestage kohtumise *piirkond*:"},
    "order_confirm":     {"ru": "📋 *Проверьте заказ:*\n\n👤 {name}\n📱 @{username}\n📞 {phone}\n📍 {address}\n💰 {total} €\n💵 Оплата наличными\n\nПодтвердить?",
                          "en": "📋 *Check order:*\n\n👤 {name}\n📱 @{username}\n📞 {phone}\n📍 {address}\n💰 {total} €\n💵 Cash payment\n\nConfirm?",
                          "et": "📋 *Kontrollige:*\n\n👤 {name}\n📱 @{username}\n📞 {phone}\n📍 {address}\n💰 {total} €\n💵 Tasumine sularahas\n\nKinnitada?"},
    "✅ Подтвердить":    {"ru": "✅ Подтвердить", "en": "✅ Confirm",  "et": "✅ Kinnita"},
    "✏️ Изменить":      {"ru": "✏️ Изменить",   "en": "✏️ Edit",    "et": "✏️ Muuda"},
    "order_placed":      {"ru": "🎉 *Заказ #{order_id} оформлен!*\n\nНапишите продавцу чтобы договориться о встрече.",
                          "en": "🎉 *Order #{order_id} placed!*\n\nMessage the seller to arrange a meeting.",
                          "et": "🎉 *Tellimus #{order_id} esitatud!*\n\nKirjutage müüjale kohtumise kokkuleppimiseks."},
    "receipt":           {"ru": "🧾 *ЧЕК #{order_id}*\n👤 {name}\n📱 @{username} | 📞 {phone}\n📍 {address}\n\n{items}\n💰 *{total} €* (наличными)",
                          "en": "🧾 *RECEIPT #{order_id}*\n👤 {name}\n📱 @{username} | 📞 {phone}\n📍 {address}\n\n{items}\n💰 *{total} €* (cash)",
                          "et": "🧾 *KVIITUNG #{order_id}*\n👤 {name}\n📱 @{username} | 📞 {phone}\n📍 {address}\n\n{items}\n💰 *{total} €* (sularaha)"},
    "new_order_admin":   {"ru": "🔔 *НОВЫЙ ЗАКАЗ #{order_id}*\n👤 {name}\n📱 @{username} | 📞 {phone}\n📍 {address}\n💰 {total} €",
                          "en": "🔔 *NEW ORDER #{order_id}*\n👤 {name}\n📱 @{username} | 📞 {phone}\n📍 {address}\n💰 {total} €",
                          "et": "🔔 *UUS TELLIMUS #{order_id}*\n👤 {name}\n📱 @{username} | 📞 {phone}\n📍 {address}\n💰 {total} €"},

    # ── МОИ ЗАКАЗЫ ────────────────────────────────────────────────────────────
    "no_orders":         {"ru": "📦 У вас нет заказов.", "en": "📦 No orders yet.", "et": "📦 Tellimusi pole."},
    "order_card":        {"ru": "📦 *Заказ #{id}*\n📅 {date} | 📊 {status}\n💰 {total} €",
                          "en": "📦 *Order #{id}*\n📅 {date} | 📊 {status}\n💰 {total} €",
                          "et": "📦 *Tellimus #{id}*\n📅 {date} | 📊 {status}\n💰 {total} €"},
    "❌ Отменить заказ": {"ru": "❌ Отменить заказ", "en": "❌ Cancel order", "et": "❌ Tühista tellimus"},

    # ── СТАТУСЫ ───────────────────────────────────────────────────────────────
    "searching":         {"ru": "🔍 Поиск",           "en": "🔍 Searching",       "et": "🔍 Otsing"},
    "ordered":           {"ru": "📋 Заказано",         "en": "📋 Ordered",         "et": "📋 Tellitud"},
    "in_transit":        {"ru": "🚚 В пути",           "en": "🚚 In Transit",      "et": "🚚 Teel"},
    "arrived":           {"ru": "📬 Готов к выдаче",  "en": "📬 Ready for pickup","et": "📬 Valmis"},
    "delivered":         {"ru": "✅ Передан",          "en": "✅ Delivered",       "et": "✅ Üle antud"},
    "cancelled":         {"ru": "❌ Отменён",          "en": "❌ Cancelled",       "et": "❌ Tühistatud"},
    "status_updated":    {"ru": "📢 *Заказ #{order_id}:*\n{status}", "en": "📢 *Order #{order_id}:*\n{status}", "et": "📢 *Tellimus #{order_id}:*\n{status}"},
    "arrived_note":      {"ru": "\n\n🤝 Напишите продавцу чтобы договориться о встрече! Оплата наличными.",
                          "en": "\n\n🤝 Message the seller to arrange a meeting! Cash payment.",
                          "et": "\n\n🤝 Kirjutage müüjale kohtumise kokkuleppimiseks! Tasumine sularahas."},

    # ── РАЗМЕР ────────────────────────────────────────────────────────────────
    "size_intro":        {"ru": "📏 Введите рост и вес — подберу размер.", "en": "📏 Enter height and weight.", "et": "📏 Sisestage pikkus ja kaal."},
    "enter_height":      {"ru": "📏 Рост (см), например 175:", "en": "📏 Height (cm), e.g. 175:", "et": "📏 Pikkus (cm), nt 175:"},
    "enter_weight":      {"ru": "⚖️ Вес (кг), например 70:", "en": "⚖️ Weight (kg), e.g. 70:", "et": "⚖️ Kaal (kg), nt 70:"},
    "size_result":       {"ru": "✅ Ваш размер: *{size}* (рост {h} см, вес {w} кг)", "en": "✅ Your size: *{size}* (height {h} cm, weight {w} kg)", "et": "✅ Teie suurus: *{size}* (pikkus {h} cm, kaal {w} kg)"},
    "invalid_number":    {"ru": "❌ Введите число.", "en": "❌ Enter a number.", "et": "❌ Sisestage arv."},
    "invalid_name":      {
        "ru": "❌ Введите настоящее имя — только буквы (например: *Иван* или *Anna*):",
        "en": "❌ Enter a real name — letters only (e.g. *Anna* or *Ivan*):",
        "et": "❌ Sisestage pärisnimi — ainult tähed (nt *Anna* või *Ivan*):",
    },
    "invalid_phone":     {
        "ru": "❌ Введите эстонский номер телефона — 8 цифр, начинается с 5 или 8\n(например: *53412345* или *87654321*):",
        "en": "❌ Enter an Estonian phone number — 8 digits, starts with 5 or 8\n(e.g. *53412345* or *87654321*):",
        "et": "❌ Sisestage Eesti telefoninumber — 8 numbrit, algab 5 või 8-ga\n(nt *53412345* või *87654321*):",
    },

    # ── РЕФЕРАЛЫ ─────────────────────────────────────────────────────────────
    "referral_info":     {"ru": "🔗 *Ваша ссылка:*\n`{link}`\n\n👥 Приглашено: *{count}*\n💰 Баланс: *{balance} €*\n\n🎁 +{bonus}€ за каждого друга!",
                          "en": "🔗 *Your link:*\n`{link}`\n\n👥 Invited: *{count}*\n💰 Balance: *{balance} €*\n\n🎁 +{bonus}€ per friend!",
                          "et": "🔗 *Teie link:*\n`{link}`\n\n👥 Kutsutud: *{count}*\n💰 Saldo: *{balance} €*\n\n🎁 +{bonus}€ iga sõbra eest!"},
    "referral_welcome":  {"ru": "👋 Вас пригласил *{name}*!", "en": "👋 You were invited by *{name}*!", "et": "👋 Teid kutsus *{name}*!"},
    "referral_bonus":    {"ru": "🎁 Ваш друг сделал заказ! +{bonus} € на баланс!", "en": "🎁 Your friend ordered! +{bonus} € added!", "et": "🎁 Teie sõber tellis! +{bonus} € lisatud!"},

    # ── ОТЗЫВЫ ───────────────────────────────────────────────────────────────
    "rate_order":        {"ru": "⭐ Оцените заказ #{order_id}:", "en": "⭐ Rate order #{order_id}:", "et": "⭐ Hinnake tellimust #{order_id}:"},
    "enter_comment":     {"ru": "💬 Комментарий (или /skip):", "en": "💬 Comment (or /skip):", "et": "💬 Kommentaar (või /skip):"},
    "review_saved":      {"ru": "✅ Спасибо за отзыв!", "en": "✅ Thank you!", "et": "✅ Täname!"},

    # ── QC ───────────────────────────────────────────────────────────────────
    "qc_received":       {"ru": "📸 *Фото QC — Заказ #{order_id}*\nПосмотрите и решите:", "en": "📸 *QC Photo — Order #{order_id}*\nReview and decide:", "et": "📸 *QC foto — Tellimus #{order_id}*\nVaadake ja otsustage:"},
    "✅ Принять":        {"ru": "✅ Принять", "en": "✅ Accept", "et": "✅ Kinnitan"},
    "❌ Отклонить":      {"ru": "❌ Отклонить", "en": "❌ Reject", "et": "❌ Keeldun"},
    "qc_accepted":       {"ru": "✅ QC принято! Товар скоро передадут.", "en": "✅ QC accepted!", "et": "✅ QC kinnitatud!"},
    "qc_rejected":       {"ru": "❌ QC отклонено. Решим проблему.", "en": "❌ QC rejected.", "et": "❌ QC tagasi lükatud."},

    # ── НАСТРОЙКИ / ПРОФИЛЬ ──────────────────────────────────────────────────
    "settings_menu":     {"ru": "⚙️ *Настройки*:", "en": "⚙️ *Settings*:", "et": "⚙️ *Seaded*:"},
    "👤 Профиль":        {"ru": "👤 Мой профиль", "en": "👤 My Profile", "et": "👤 Minu profiil"},
    "🌍 Язык":           {"ru": "🌍 Изменить язык", "en": "🌍 Change Language", "et": "🌍 Muuda keelt"},
    "profile_info":      {"ru": "👤 *Профиль*\n━━━━━━━━━━━━━━\n🆔 `{tg_id}`\n👤 {name}\n🌍 {lang}\n💰 {balance} €\n📦 Заказов: {orders}",
                          "en": "👤 *Profile*\n━━━━━━━━━━━━━━\n🆔 `{tg_id}`\n👤 {name}\n🌍 {lang}\n💰 {balance} €\n📦 Orders: {orders}",
                          "et": "👤 *Profiil*\n━━━━━━━━━━━━━━\n🆔 `{tg_id}`\n👤 {name}\n🌍 {lang}\n💰 {balance} €\n📦 Tellimusi: {orders}"},

    # ── АДМИН — ТОВАРЫ ────────────────────────────────────────────────────────
    "admin_products_menu": {"ru": "📦 *Управление товарами*:", "en": "📦 *Products*:", "et": "📦 *Tooted*:"},
    "➕ Добавить":       {"ru": "➕ Добавить товар", "en": "➕ Add Product", "et": "➕ Lisa toode"},
    "✏️ Редактировать": {"ru": "✏️ Редактировать", "en": "✏️ Edit", "et": "✏️ Muuda"},
    "🗑 Удалить":        {"ru": "🗑 Удалить товар", "en": "🗑 Delete", "et": "🗑 Kustuta"},
    "enter_prod_name":   {"ru": "📝 Название товара:", "en": "📝 Product name:", "et": "📝 Toote nimi:"},
    "enter_prod_price":  {"ru": "💰 Цена (€), например 29.99:", "en": "💰 Price (€), e.g. 29.99:", "et": "💰 Hind (€), nt 29.99:"},
    "enter_prod_desc":   {"ru": "📄 Описание:", "en": "📄 Description:", "et": "📄 Kirjeldus:"},
    "send_prod_photo":   {"ru": "📸 Отправьте фото:", "en": "📸 Send photo:", "et": "📸 Saatke foto:"},
    "choose_cat_admin":  {"ru": "📂 Выберите категорию:", "en": "📂 Choose category:", "et": "📂 Valige kategooria:"},
    "product_added":     {"ru": "✅ Товар добавлен!", "en": "✅ Product added!", "et": "✅ Toode lisatud!"},
    "product_updated":   {"ru": "✅ Товар обновлён!", "en": "✅ Updated!", "et": "✅ Uuendatud!"},
    "product_deleted":   {"ru": "✅ Товар удалён.", "en": "✅ Deleted.", "et": "✅ Kustutatud."},
    "no_products_admin": {"ru": "❌ Товаров нет.", "en": "❌ No products.", "et": "❌ Tooteid pole."},
    "select_product":    {"ru": "👇 Выберите товар:", "en": "👇 Select product:", "et": "👇 Valige toode:"},

    # ── АДМИН — ЗАКАЗЫ ────────────────────────────────────────────────────────
    "no_orders_admin":   {"ru": "❌ Заказов нет.", "en": "❌ No orders.", "et": "❌ Tellimusi pole."},
    "order_not_found":   {"ru": "❌ Заказ не найден.", "en": "❌ Not found.", "et": "❌ Ei leitud."},
    "status_changed":    {"ru": "✅ Статус обновлён!", "en": "✅ Updated!", "et": "✅ Uuendatud!"},

    # ── АДМИН — QC ───────────────────────────────────────────────────────────
    "enter_order_id_qc": {"ru": "🔢 ID заказа для QC:", "en": "🔢 Order ID for QC:", "et": "🔢 Tellimuse ID QC jaoks:"},
    "send_qc_photo":     {"ru": "📸 Отправьте QC фото:", "en": "📸 Send QC photo:", "et": "📸 Saatke QC foto:"},
    "qc_sent":           {"ru": "✅ QC отправлено!", "en": "✅ QC sent!", "et": "✅ QC saadetud!"},

    # ── ОБЩЕЕ ─────────────────────────────────────────────────────────────────
    "cancelled_action":  {"ru": "❌ Отменено.", "en": "❌ Cancelled.", "et": "❌ Tühistatud."},
    "error":             {"ru": "❌ Ошибка. Попробуйте снова.", "en": "❌ Error.", "et": "❌ Viga."},
    "no_reviews":        {"ru": "❌ Отзывов нет.", "en": "❌ No reviews.", "et": "❌ Arvustusi pole."},
    "no_referrals":      {"ru": "❌ Рефералов нет.", "en": "❌ No referrals.", "et": "❌ Suunamisi pole."},

    # ── ЧАТА С ПРОДАВЦОМ ──────────────────────────────────────────────────────
    "support_intro":     {"ru": "💬 *Чат с продавцом*\n\nДоговоритесь о месте встречи и оплате наличными.\n\n✍️ Напишите сообщение:",
                          "en": "💬 *Seller Chat*\n\nArrange meeting place and cash payment.\n\n✍️ Write your message:",
                          "et": "💬 *Vestlus müüjaga*\n\nLeppige kokku kohtumiskoht ja tasumine.\n\n✍️ Kirjutage sõnum:"},
    "support_sent":      {"ru": "✅ Сообщение отправлено продавцу!", "en": "✅ Message sent!", "et": "✅ Sõnum saadetud!"},
    "support_reply_hdr": {"ru": "🏪 *Продавец:*", "en": "🏪 *Seller:*", "et": "🏪 *Müüja:*"},
}

LANG_NAMES = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "et": "🇪🇪 Eesti"}


def gt(key: str, lang: str = "ru", **kw) -> str:
    """Get translated text. Falls back to ru then key."""
    lang = lang if lang in ("ru", "en", "et") else "ru"
    entry = T.get(key, {})
    text = entry.get(lang) or entry.get("ru") or key
    try:
        return text.format(**kw) if kw else text
    except Exception:
        return text

