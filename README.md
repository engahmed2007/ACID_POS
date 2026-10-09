# برنامج بيع وإدارة مخزون ماء النار

برنامج سطح مكتب بلغة Python لإدارة بيع وشراء ماء النار بالجملة والقطاعي،
مع مخزون، سعر ثابت للبيع، فواتير وخصومات، حسابات عملاء (آجل/ديون)،
تقارير بتقويم لاختيار الفترة، وصلاحيات موظفين مفصّلة يتحكم فيها المدير.

## 1. هيكل المشروع

```
acid_pos/
├── main.py                     # نقطة تشغيل البرنامج
├── config.py                   # كل الإعدادات الثابتة في مكان واحد
├── requirements.txt             # المكتبة الخارجية الوحيدة (tkcalendar)
├── assets/                       # أيقونة البرنامج (icon.ico) والشعار (logo.png)
├── database/
│   ├── schema.sql               # مخطط كل الجداول
│   └── db_manager.py            # طبقة الاتصال بـ SQLite + ترقية القاعدة تلقائياً
├── models/
│   └── models.py                 # أشكال البيانات (Product, Invoice, Customer...)
├── auth/
│   ├── auth_manager.py           # تسجيل الدخول، تشفير كلمات المرور، الجلسة، الصلاحيات
│   └── permissions.py            # تعريف كل الصلاحيات القابلة للتفويض للموظفين
├── services/                     # كل منطق العمل (Business Logic) بعيد عن الواجهة
│   ├── inventory_service.py      # المخزون وحركته
│   ├── pricing_service.py        # السعر الثابت للبيع
│   ├── sales_service.py          # الفواتير والبيع والخصم
│   ├── customer_service.py       # العملاء والديون والدفعات
│   ├── reports_service.py        # كل التقارير
│   ├── employee_service.py       # إدارة الموظفين وصلاحياتهم
│   ├── backup_service.py         # النسخ الاحتياطي
│   └── export_service.py         # تصدير التقارير CSV
├── utils/
│   ├── formatting.py             # تنسيق الأرقام (بدون كسور زيادة) ومشترك بين كل الطبقات
│   └── ui_helpers.py             # الأيقونة، وضع ملء الشاشة، تحميل الشعار
├── gui/                           # الواجهة الرسومية (Tkinter) فقط - بدون أي SQL مباشر
│   ├── login_window.py            # الشاشة الوحيدة اللي مش Full Screen
│   ├── main_window.py            # الشاشة الرئيسية - شاشة واحدة لكل أيقونة
│   ├── sales_window.py           # شاشة البيع والفواتير + الخصم
│   ├── inventory_window.py       # شاشة المخزون + شاشة السعر الثابت للبيع
│   ├── customers_window.py       # حسابات العملاء (تبويب العملاء + تبويب المديونيات)
│   ├── reports_window.py         # شاشة التقارير بتقويم لاختيار الفترة
│   ├── employees_window.py       # إدارة الموظفين وصلاحياتهم (مدير فقط)
│   └── widgets/common.py         # عناصر وتنسيقات مشتركة (بما فيها منتقي التاريخ)
└── data/                          # تُنشأ تلقائياً: قاعدة البيانات + النسخ الاحتياطية + التصدير
```

**الفصل بين الطبقات:** الواجهة (`gui/`) لا تتحدث مع قاعدة البيانات مباشرة أبداً؛
هي بس بتنادي دوال من `services/`. والـ `services/` بيتعامل مع `database/db_manager.py`
فقط، ومش عارف حاجة عن SQLite تحديداً. فلو احتجت مستقبلاً تنقل لـ PostgreSQL،
هتغيّر ملف `db_manager.py` بس، وكل باقي البرنامج هيفضل شغال زي ما هو.

## 2. المميزات الأساسية

- **شاشة واحدة فقط لكل أيقونة** — لو فتحت شاشة وهي مفتوحة بالفعل، البرنامج
  بينقلها لقدامك بدل ما يفتح نسخة جديدة منها. وتقرير المديونيات بقى تبويب
  جوه شاشة العملاء نفسها، مش نافذة منفصلة.
- **كل الشاشات Full Screen ما عدا تسجيل الدخول** — عشان تسجيل الدخول شاشة
  سريعة ومفروض تفضل بحجمها الطبيعي.
- **صلاحيات مفصّلة يتحكم فيها المدير** — من شاشة "إدارة الموظفين"، اختار أي
  موظف من القائمة وحدد بالظبط أي شاشات مسموح له يدخلها (بيع، مخزون، سعر،
  عملاء، تقارير، حذف فواتير). المدير نفسه عنده كل الصلاحيات تلقائياً.
- **رقم الفاتورة ظاهر من الأول** — شاشة البيع بتعرض رقم الفاتورة القادمة
  فوق قبل ما تحفظ، وبيتحدث بعد كل عملية حفظ.
- **سعر ثابت للبيع** — تسجّله مرة وتفضل عليه، وتعدّله بس وقت ما السعر في
  السوق يتغيّر (مش لازم تدخله كل يوم من الأول). كل تعديل بيتسجل تاريخياً.
- **خصم على الفاتورة** — تقدر تدي خصم كمبلغ ثابت بالجنيه أو كنسبة مئوية،
  والشاشة بتوريك الإجمالي قبل الخصم وقيمة الخصم والإجمالي النهائي أول
  بأول وانت لسه بتكتب. الخصم بيتسجل في الفاتورة وبيتحسب في كل التقارير.
- **كود مميز لكل عميل** — كل عميل بياخد كود تلقائي (مثال: C0001) وقت
  التسجيل، وبتقدر تدور بيه أو بالاسم في أي مكان.
- **البيع الآجل بقى بالبحث والاختيار مش بالكتابة** — شاشة البيع بتظهر
  خانة بحث بالاسم أو الكود + قائمة اختيار للعميل، وزرار "عميل جديد" لو
  مش موجود، لكن بس لما تفعّل "فاتورة آجلة". **البيع النقدي المباشر
  مايظهرش فيه أي حقل اسم عميل خالص** — القسم ده بيختفي تماماً في حالة
  البيع النقدي.
- **تنسيق أرقام ذكي** — أي رقم صحيح بيتعرض من غير فاصلة عشرية أو أصفار
  زيادة (1000 مش 1000.00)، والكسور الحقيقية بس هي اللي بتتعرض (1000.5).
- **تقويم لاختيار فترة التقارير** — حقول التاريخ في كل شاشات التقارير
  (المبيعات، الأرباح، البحث عن فاتورة) بشكل تقويم تضغط عليه وتختار
  اليوم بالماوس، مع ترتيب واضح لصفوف البحث والفلاتر وزرار النطاق.
- **أيقونة وشعار البرنامج** — أيقونة البرنامج (`assets/icon.ico`) ظاهرة في
  شريط العنوان لكل الشاشات، والشعار (`assets/logo.png`) ظاهر في شاشة تسجيل
  الدخول والشاشة الرئيسية.

- **مفيش خاصية طباعة فواتير** — الحفظ مباشر بدون أي سؤال عن الطباعة،
  تبسيطاً لسير العمل اليومي في المحل.
- **جاهز للتحويل لملف .exe (PyInstaller)** — `config.py` بيفرّق بين
  الملفات "للقراءة فقط" (الأيقونة، الشعار، مخطط قاعدة البيانات) اللي
  بتتحزم جوه الـ exe، والملفات "للقراءة والكتابة" (قاعدة البيانات،
  النسخ الاحتياطية، التصدير) اللي بتتحفظ بجانب الـ exe نفسه عشان
  متتمسحش لما تقفل البرنامج. راجع القسم رقم 8 تحت لتفاصيل التحزيم.

## 3. القرارات التقنية المهمة

- **الواجهة: Tkinter + tkcalendar فقط** — Tkinter نفسه مدمج جوه بايثون، ومكتبة
  `tkcalendar` (لعنصر التقويم في التقارير) هي المكتبة الخارجية الوحيدة
  المطلوبة، وخفيفة جداً وسهلة التنصيب على أي جهاز.

- **كلمات المرور مشفّرة بـ PBKDF2-HMAC-SHA256** مع "ملح" (salt) عشوائي مختلف
  لكل موظف، و200,000 دورة تشفير. الكلمة الأصلية مش بتتخزن في أي مكان أبداً.

- **حذف الفواتير "منطقي" وليس فعلي (Soft Delete)** — بترجع المخزون والدين
  تلقائياً، والسجل نفسه بيفضل موجود في قاعدة البيانات، ويتسجل في
  `audit_log` مين حذفها وإمتى وليه.

- **حماية من الرصيد السالب** — أي محاولة بيع كمية أكبر من المتاح بالمخزون
  بترفض فوراً برسالة واضحة.

- **الخصم محسوب على مستوى الفاتورة ككل** (مش موزّع على كل صنف لوحده)، وده
  اللي بيخلي تقرير الأرباح يعرض "الربح الإجمالي" و"صافي الربح بعد الخصم"
  كرقمين منفصلين، عشان تشوف تأثير الخصومات على أرباحك بوضوح.

- **صلاحيات الموظفين مخزّنة كنص مفصول بفواصل** في عمود `permissions`،
  وبيتحول لمجموعة (`set`) في الكود عن طريق `auth/permissions.py`. إدارة
  الموظفين نفسها (إضافة/تعطيل/تعديل صلاحيات) مقصورة على المدير دايماً
  ومش من ضمن الصلاحيات القابلة للتفويض، حفاظاً على أمان النظام.

- **تصدير التقارير بصيغة CSV** — بيتفتح مباشرة في Excel، ومدمج في بايثون
  بدون أي مكتبات خارجية إضافية.

## 4. طريقة التشغيل

```bash
cd acid_pos
pip install -r requirements.txt
python3 main.py
```

على أجهزة لينكس، لو ظهرت رسالة إن `tkinter` مش موجود، ثبّته أولاً:
```bash
sudo apt-get install python3-tk
```

**أول مرة تشغّل البرنامج:** هيتنشئ حساب مدير افتراضي تلقائياً:
- اسم المستخدم: `admin`
- كلمة المرور: `admin123`

⚠️ **مهم جداً:** غيّر كلمة مرور هذا الحساب فوراً من شاشة "إدارة الموظفين"
بعد أول دخول، أو أنشئ حساب مدير جديد بكلمة مرور خاصة بيك وعطّل حساب `admin`.

## 5. ترتيب استخدام الشاشات لأول مرة

1. **تسجيل الدخول** بحساب `admin`
2. **إدارة المخزون** → أضف الأنواع المختلفة لماء النار، وسجّل أول توريد كمية
3. **السعر الثابت للبيع** → سجّل سعر الكيلو الحالي لكل نوع
4. **إدارة الموظفين والصلاحيات** → أضف حسابات باقي الموظفين، وحدد لكل واحد
   بالظبط أي شاشات مسموح له يدخلها
5. من هنا البرنامج جاهز لعمل فواتير بيع (مع إمكانية الخصم) من شاشة
   **فاتورة بيع جديدة**

## 6. النسخ الاحتياطي

اضغط زرار "نسخة احتياطية الآن" من الشاشة الرئيسية في أي وقت. النسخ بتتحفظ
في `data/backups/` باسم فيه التاريخ والوقت. ينصح تعمل نسخة كل يوم قبل قفل المحل.

## 7. ملاحظة أمان مهمة

هذا البرنامج مخصص لإدارة المخزون والمبيعات والحسابات فقط، ولا يتضمن أي معلومات
عن كيفية التصنيع أو التركيز الكيميائي للمنتج — فقط الكمية والسعر والبيانات
التجارية العادية، تماماً مثل أي برنامج نقاط بيع لأي منتج تجاري آخر.

## 8. تحويل البرنامج لملف .exe (اختياري)

لو حبيت تحوّل البرنامج لملف تنفيذي واحد (`.exe`) بواسطة PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico ^
    --add-data "assets;assets" --add-data "database/schema.sql;database" ^
    main.py
```

(على لينكس/ماك استخدم `:` بدل `;` فاصل بين المسارين مع `--add-data`)

الكود في `config.py` مبني عشان يتعامل صح مع الحالتين تلقائياً:
- **ملفات القراءة فقط** (`assets/icon.ico`, `assets/logo.png`,
  `database/schema.sql`) بيدور عليها `resource_path()` جوه مجلد
  PyInstaller المؤقت (`sys._MEIPASS`) وقت التشغيل كملف .exe.
- **ملفات القراءة والكتابة** (قاعدة البيانات، النسخ الاحتياطية،
  التصدير) بيحفظها `data_path()` بجانب ملف الـ .exe نفسه (`sys.executable`)
  مش في المجلد المؤقت، عشان تفضل موجودة بعد ما تقفل البرنامج وتفتحه تاني.

مفيش أي تعديل تاني مطلوب في الكود - الفرق ده متأصل في `config.py` من الأول.
# ACID_POS — Point of Sale & Inventory Management System

A desktop application designed to simplify sales operations, product management, and inventory tracking for small businesses and retail stores.

## Overview

**ACID_POS** is a desktop-based Point of Sale (POS) and Inventory Management System developed to help store owners manage products, track stock quantities, monitor inventory levels, and organize daily sales operations through a user-friendly interface.

The project focuses on making routine store management tasks easier, improving inventory visibility, and reducing manual work.

## Features

* **Product Management:** Organize and manage product information.
* **Inventory Tracking:** Monitor available stock quantities.
* **Stock Management:** Record incoming stock and update product quantities.
* **Low-Stock Alerts:** Identify products that fall below their configured stock thresholds.
* **Sales Management:** Support store sales workflows.
* **Database Integration:** Store and manage application data.
* **Desktop Interface:** Provide a dedicated interface for daily store operations.

*Note: The feature list should be adjusted to match the functionality implemented in the current version.*

## Technologies Used

* **Python** — Application development
* **Tkinter / CustomTkinter** — Desktop user interface, where applicable
* **SQL** — Database operations, where applicable
* **Git & GitHub** — Version control and project hosting

## Project Structure

The following is an example structure. Update it to match the actual files in your repository.

```text
ACID_POS/
├── app.py
├── database/
│   └── schema.sql
├── assets/
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

* Python 3.10 or a compatible version supported by the project.
* pip (Python package installer).
* The project source code.

### Installation

1. Clone the repository:

   ```bash
   git clone <YOUR_REPOSITORY_URL>
   ```

2. Navigate to the project directory:

   ```bash
   cd ACID_POS
   ```

3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate the virtual environment on Windows:

   ```bash
   .venv\Scripts\activate
   ```

5. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run the application, if `app.py` is the project's entry point:

   ```bash
   python app.py
   ```

## Screenshots

Screenshots of the application's interface can be added here to demonstrate the main features, including the dashboard, product management, inventory, and sales screens.

Example:

```markdown
![Application Dashboard](assets/dashboard.png)
```

## Project Goals

* Simplify point-of-sale operations.
* Improve inventory tracking and stock visibility.
* Reduce repetitive manual tasks.
* Provide a practical desktop solution for small retail businesses.

## Future Improvements

Potential enhancements include:

* Sales and inventory analytics dashboards.
* Detailed sales reports and export options.
* Improved product search and filtering.
* Enhanced reporting and business insights.
* Additional inventory management capabilities.

## About the Developer

Developed as a practical software project focused on desktop application development, inventory management, and retail operations.

## License

Choose and add an appropriate open-source license before allowing others to reuse or distribute the project.
