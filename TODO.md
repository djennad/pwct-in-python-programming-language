# TODO — المهام المتبقية

> جزء من توثيق المشروع:
> [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md) · [ARCHITECTURE](ARCHITECTURE.md) · [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [CURRENT_STATE](CURRENT_STATE.md) · [DECISIONS](DECISIONS.md)
>
> الرموز: 🔴 مهم/عاجل · 🟠 متوسط · 🟢 تحسين · `[ ]` لم يبدأ · `[x]` تم

---

## المرحلة 7: التثبيت والاختبارات (التالية)

- [ ] 🔴 اختبارات وحدة `tests/test_engine.py`: NEWSTEP و SETMARK و PUTMARK و TEST و Modify (الحفاظ على الأبناء، والإدراج في المكان الصحيح، والحذف).
- [ ] 🔴 `tests/test_codegen.py`: الإزاحة، و `pass`، و `<pwct:...>`، و TOFILE، و linemap.
- [ ] 🔴 `tests/test_rules.py`: أنواع الخطوات، والقفل، و `allow` و `requires_step`، و `auto_pairs`.
- [x] `tests/test_components.py`: شجرة المجالات، والمفاتيح القديمة، وحماية مكونات المستخدم — v1.3.
- [x] حماية مكونات المستخدم: `write_components()` يحذف فقط الملفات المسجلة في `_generated.txt` — v1.3 (D42).
- [ ] 🟠 نقل أداة اختبار الواجهة (snap والسيناريوهات) إلى `tools/ui_tests/`، مع تخطي اللقطات إذا لم يوجد Pillow.
- [x] البحث عن المكوّن باسم ملفه عند فقد المفتاح، وتحديث المفاتيح عند الفتح (D4، D41) — v1.3.
- [ ] 🟠 تنبيه قبل أن يحذف Modify فرعًا فيه خطوات للمستخدم (D7).

## شجرة المجالات (مثل HarbourPWCT)

- [ ] 🟢 مكونات لمجالات الأصل التي لا تظهر الآن لأنها فارغة: Main Menu و Status Bar و Toolbar و Drawing (Canvas) و Sound و Operations/Logic.
- [ ] 🟢 استخدام `ClassicTree` في نافذة Domain Tree و Component Designer أيضًا (ما زالتا بـ `ttk.Treeview`).

## المرحلة 8: مكونات أغنى للغات الجديدة

- [ ] 🟠 Classes: Class و Constructor و Method و Field و New Object، للغات C# و Java و JS.
- [ ] 🟠 Files: قراءة وكتابة الملفات، للغات C و C# و Java و JS.
- [ ] 🟠 Collections: `List<T>` و `Dictionary` في C#، و `ArrayList` و `HashMap` في Java، ودوال المصفوفات في JS.
- [ ] 🟠 Switch/Case و Try/Catch.
- [ ] 🟢 دوال نصوص إضافية (Substring و IndexOf و Replace و Split).
- [ ] 🟢 واجهات رسومية: C# WinForms (Form و Button و Label و TextBox و Events)، و Java Swing.
- [ ] 🟢 أمثلة جديدة لكل لغة، وإضافتها إلى `test_samples.py`.

## المرحلة 9: Form Designer

- [x] مصمم مرئي للنوافذ يولّد خطوات عبر المكونات (Python/Tkinter) — v1.2
- [x] تفعيل Ctrl+F لـ Form Designer كما في الأصل، مع نقل البحث إلى Ctrl+Shift+F و F3.
- [x] مكونات Text Area و Check Box و List Box، وإنشاء دالة الحدث بالنقر المزدوج على الزر.
- [x] Create Window كتلة (Start Here + End of Window فيها mainloop) مع خيار Show، وترقية الملفات القديمة — v1.3 (D40).
- [ ] 🟠 Undo و Redo داخل المصمم.
- [ ] 🟠 نسخ ولصق العناصر، وتحديد أكثر من عنصر معًا (Ctrl+Click أو مستطيل تحديد).
- [ ] 🟢 أدوات المحاذاة: محاذاة لليسار أو للأعلى، وتوحيد العرض، وتوزيع المسافات.
- [ ] 🟢 عناصر إضافية: Combo Box و Radio Button و Frame و Image و Scale و Menu (مصمم قوائم).
- [ ] 🟢 خاصية Tab Order، وأحداث أخرى غير On Click (مثل Enter أو Change).
- [ ] 🟢 Form Designer لـ C# WinForms و Java Swing: مكونات Window و Controls مع mapping `designer`.
- [ ] 🟢 تنبيه في المصمم عندما يخرج عنصر عن حدود النافذة.

## المرحلة 10: واجهة عربية

- [ ] 🟠 ملفات نصوص `ui_lang/en.json` و `ar.json`، ودالة `tr()`.
- [ ] 🟠 استبدال النصوص الثابتة في `ui/*.py`.
- [ ] 🟢 قائمة لتغيير لغة الواجهة، ودراسة RTL.

## المرحلة 11: لغات إضافية

- [ ] 🟠 HarbourPWCT، لغة الأصل (يتطلب مترجم Harbour).
- [ ] 🟢 Go و Ruby و PHP و Lua.

## المرحلة 12: بقية ميزات الأصل

- [ ] 🟢 Packages: تصدير المكونات وتثبيتها كحزمة.
- [ ] 🟢 Time Machine Documentation Generator (لقطات وصفحة HTML).
- [ ] 🟢 قواعد `NoDuplication` و `Scope` و `List:` من ملف `.RULES`.
- [ ] 🟢 ملفات Intellisense لكل لغة، مع قائمة تظهر أثناء الكتابة بدل Ctrl+Space فقط.
- [ ] 🟢 خيار مطابقة البادئة في `SELECTSTEPBYNAME` كما في الأصل.
- [ ] 🟢 دعم متغيرات الـ mask بالشكل `[...]` (مع الحذر من قوائم بايثون).
- [ ] 🟢 الصوت في Time Machine.

## المرحلة 13: التوزيع

- [ ] 🟢 ملف exe بـ PyInstaller.
- [ ] 🟢 برنامج تثبيت، وربط امتداد `.pwct` بالبرنامج.
- [ ] 🟢 اختبار على Linux و macOS.
- [ ] 🟢 خيار DPI-aware مع تحجيم الإحداثيات (D2).

## ما لم يُختبر آليًا بعد (للتحقق اليدوي)

- [ ] 🟠 نافذة الـ Console الحقيقية عند Ctrl+R، لكل لغة.
- [ ] 🟠 الإدخال التفاعلي في Node على Windows (`fs.readSync` في Console حقيقية).
- [ ] 🟢 مثال الواجهة الرسومية `05_GUI_Calculator` يدويًا.
- [ ] 🟢 نافذة Programming Languages List: إنشاء لغة جديدة واستخدامها من البداية للنهاية.

## أُنجز

- [x] تحليل السورس الأصلي، وقارئ DBF، وتحويل الأيقونات.
- [x] النواة والواجهة (v1.0) + 67 مكوّنًا لبايثون + 6 أمثلة.
- [x] كل أوامر الـ Code Mask ومتغيرات `<T_...>` مع Automatic Matching.
- [x] لغات متعددة (v1.1): C و C# و Java و JavaScript، والبناء والتشغيل، و VPL Compiler بالمترجم، و Programming Languages List.
- [x] نقل مكوّني المستخدم `print` و `printo` إلى المكان الجديد.
- [x] التوثيق الكامل (7 ملفات) و `tools/test_samples.py` و `tools/dbfread.py`.
- [x] Form Designer (v1.2) + اختبارات وحدة `tests/test_forms.py`.
- [x] v1.3: إصلاح "النافذة لا تظهر" (Create Window بلا mainloop).
- [x] v1.3: Components Browser مثل الأصل بشجرة مجالات متداخلة لكل اللغات، و 19 اختبار وحدة.
