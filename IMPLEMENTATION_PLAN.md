# IMPLEMENTATION_PLAN — خطة التنفيذ

> جزء من توثيق المشروع:
> [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md) · [ARCHITECTURE](ARCHITECTURE.md) · [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) · [CURRENT_STATE](CURRENT_STATE.md) · [DECISIONS](DECISIONS.md) · [TODO](TODO.md)

---

## 1. منهجية التحويل من VFP إلى Python

1. **دراسة السورس لا تخمينه:** كل نافذة نُقلت بعد قراءة خصائصها وكودها من ملف `.scx`، وكل خوارزمية بعد قراءة ملف `.prg` الخاص بها.
2. **فصل النواة عن الواجهة:** المحرك ومولّد الكود بلا Tkinter، حتى يمكن اختبارهما بسكربتات.
3. **البيانات قبل الواجهة:** صيغة المكوّن (JSON) ← المحرك ← الواجهة.
4. **الاختبار بالتشغيل الفعلي:** كل مكوّن يُختبر ضمن أمثلة تُبنى بالمحرك نفسه، ثم تُترجم وتُشغَّل بالمترجم الحقيقي.
5. **الحفاظ على الشكل:** نفس الترتيب والأيقونات والألوان والنصوص الإنجليزية الأصلية.
6. **الانحراف عن الأصل فقط لإصلاح خطأ أو تحسين واضح**، مع تسجيل ذلك في [DECISIONS](DECISIONS.md).

## 2. المراحل المنجزة

| المرحلة | المحتوى | المخرجات | الحالة |
|---|---|---|---|
| 0. التحليل | قراءة الكود والنماذج والجداول، وتحويل الأيقونات | [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) و `tools/dbfread.py` و `assets/` | ✅ |
| 1. النواة | model و engine و codegen و rules و components و settings و runner | `pwct/*.py` | ✅ |
| 2. الواجهة | App و GoalDesigner و Browser و Interaction و Designer و Dialogs و DomainTree | `pwct/ui/*.py` | ✅ |
| 3. مكونات بايثون | 67 مكوّنًا في 12 مجالًا، و 6 أمثلة | `tools/make_components.py` و `tools/make_samples.py` | ✅ |
| 4. أوامر Code Mask كاملة | TOFILE و ADDVAR/SETVAR و MERGE…STAR ومتغيرات `<T_...>` مع Automatic Matching | `codegen.py` و `components.py` و `designer.py` | ✅ |
| 5. لغات متعددة (v1.1) | `languages.py`، وقائمة VPL، و Build/Run/Check، وملفات start.pwct، و Programming Languages List، وقاعدتا `requires_step`/`allow`، ومكونات C و C# و Java و JS | `tools/make_languages.py` و `languages/` | ✅ |
| 6. التوثيق | ملفات التوثيق السبعة + README، واختبار شامل | `*.md` و `tools/test_samples.py` | ✅ |
| 9. Form Designer (Python) | النموذج والواجهة، ومكونات الواجهة مع قسم `designer`، وإنشاء دالة الحدث، واختبارات وحدة | `pwct/forms.py` و `pwct/ui/formdesigner.py` و `tests/test_forms.py` | ✅ (v1.2) |

## 3. المراحل القادمة (بالترتيب المقترح)

> الترتيب مقترح حسب الأهمية وقلة المخاطرة. يمكن تغييره حسب أولويات صاحب المشروع.

### المرحلة 7: التثبيت والاختبارات (أولوية عالية، حجم صغير)
**الهدف:** حماية ما أُنجز قبل إضافة ميزات جديدة.
1. **اختبارات وحدة** بـ `unittest` (من مكتبة بايثون القياسية) في مجلد `tests/`:
   - `test_engine.py`: NEWSTEP و SETMARK و TEST و Modify (الحفاظ على الأبناء، والإدراج في المكان الصحيح، وحذف ما لم يعد يُولَّد).
   - `test_codegen.py`: الإزاحة، و `pass`، وأوامر `<pwct:...>`، و TOFILE، و linemap.
   - `test_rules.py`: أنواع الخطوات الستة، والقفل، و `allow` و `requires_step`.
   - `test_components.py`: `mask_tokens` و `auto_pairs` و Library.
2. **نقل أداة اختبار الواجهة** (`snap.py` والسيناريوهات) إلى `tools/ui_tests/`، على أن تعمل بدون Pillow إن لم يكن مثبتًا (تتخطى لقطات الشاشة).
3. ✅ **حماية مكونات المستخدم** (v1.3، D42): `write_components()` يحذف فقط الملفات المسجلة في `_generated.txt`.
4. ✅ **مفاتيح المكونات** (v1.3، D41): `Library.get()` يبحث باسم الملف إذا لم يوجد المفتاح، و `update_keys()` يحدّث المفاتيح عند الفتح.
- **معيار الإنجاز:** `python -m unittest` و `python tools/test_samples.py` ينجحان كلاهما.

### المرحلة 8: مكونات أغنى لـ C و C# و Java و JavaScript
1. **Classes:** C# و Java و JS (Class، و Constructor، و Method، و Field، و New Object).
2. **Files:** قراءة وكتابة الملفات في اللغات الأربع.
3. **Collections:** `List<T>` و `Dictionary` في C#، و `ArrayList` و `HashMap` في Java، ودوال المصفوفات في JS.
4. **Switch/Case**، و **Try/Catch** (C# و Java و JS)، ودوال النصوص.
5. **الواجهات الرسومية:** C# WinForms (Form و Button و Label و TextBox و Events)، و Java Swing.
6. أمثلة جديدة لكل لغة، وإضافتها إلى `test_samples.py`.
- **الملفات:** `tools/make_languages.py` (`comp()` و `by()`)، ثم تشغيل الأداة.
- **معيار الإنجاز:** مثال "Classes" ومثال "Files" لكل لغة يُبنيان ويعملان.

### المرحلة 9: Form Designer — ✅ أُنجزت للغة Python (v1.2)
المتبقي منها (Undo، والمحاذاة، وعناصر إضافية، و WinForms و Swing) موجود في [TODO](TODO.md). الوصف الأصلي للمرحلة:
الزر موجود في الأصل (`Command12` في `rpwi.scx`، واختصاره Ctrl+F).
1. مصمم مرئي للنوافذ: سحب وإفلات، وخصائص. يمكن إعادة استخدام آلية السحب في `designer.py`.
2. يولّد **خطوات** عن طريق مكونات موجودة (Create Window و Label و Button …)، ولا يكتب كودًا مباشرة، حتى يبقى كل شيء قابلًا للتعديل بـ Modify.
3. البداية بـ Python/Tkinter، ثم C# WinForms.
- **معيار الإنجاز:** تصميم نافذة الآلة الحاسبة من المصمم، ينتج نفس مثال `05_GUI_Calculator`.

### المرحلة 10: واجهة عربية (Localization)
1. ملف نصوص لكل لغة واجهة (`ui_lang/en.json` و `ar.json`)، على غرار `syslang.txt`.
2. دالة `tr(key)` في `common.py`، ثم استبدال النصوص الثابتة في `ui/*.py`.
3. قائمة لتغيير لغة الواجهة، ودراسة اتجاه RTL لشجرة الخطوات.
- **معيار الإنجاز:** كل القوائم والنوافذ تظهر بالعربية عند اختيارها.

### المرحلة 11: لغات برمجة إضافية
1. **HarbourPWCT** (اللغة الأساسية في الأصل)، ويحتاج مترجم Harbour.
2. Go و Ruby و PHP و Lua. كل لغة = تعريف في `LANGS` + مكونات أساسية + 3 أمثلة.
- **معيار الإنجاز:** مرور الأمثلة في `test_samples.py` على الأجهزة التي يتوفر فيها المترجم.

### المرحلة 12: بقية ميزات الأصل
1. **Packages:** تصدير مجموعة مكونات في ملف واحد (zip) وتثبيتها (New/Open/Install Package).
2. **Time Machine Documentation Generator:** لقطة لكل إطار زمني، وصفحة HTML.
3. قواعد `NoDuplication` و `Scope` و `List:` من ملف `.RULES`.
4. ملفات Intellisense خاصة بكل لغة.
5. الصوت في Time Machine (اختياري).

### المرحلة 13: التوزيع
1. ملف exe واحد بـ PyInstaller (مع assets و languages).
2. برنامج تثبيت (NSIS مثل الأصل)، وربط امتداد `.pwct` بالبرنامج.
3. اختبار على Linux و macOS (مسار التشغيل في الطرفية).
4. خيار DPI-aware مع تحجيم الإحداثيات (انظر D2 في DECISIONS).

## 4. قواعد العمل في المراحل القادمة

- قبل أي تعديل وبعده: `python tools/test_samples.py`.
- أي قرار يخالف الأصل يُسجَّل في [DECISIONS](DECISIONS.md).
- بعد كل مرحلة: تحديث [CURRENT_STATE](CURRENT_STATE.md) و [TODO](TODO.md).
- تغيير الـ masks يتم في `tools/make_*.py` وليس في ملفات JSON مباشرة، لأن الأداة تعيد توليدها.
- لا يُضاف أي تبعية خارجية لوقت التشغيل إلا بقرار مسجَّل.
