# CURRENT_STATE — أين توقفنا

> جزء من توثيق المشروع:
> [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md) · [ARCHITECTURE](ARCHITECTURE.md) · [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [DECISIONS](DECISIONS.md) · [TODO](TODO.md)
>
> **آخر تحديث: 2026-09-24**

---

## 1. الحالة باختصار

- **الإصدار:** PyPWCT **1.3**: Components Browser بشجرة مجالات متداخلة مثل الأصل، وإصلاح مكوّن Create Window (النافذة تظهر وحدها)، بعد إضافة **Form Designer** في 1.2. يعمل ومستقر، وكل الاختبارات ناجحة.
- **المراحل من 0 إلى 6 منجزة**، والمرحلة 9 (Form Designer) منجزة للغة Python. انظر [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md).
- **اختبارات الوحدة:** `python -m unittest discover -s tests` نجحت، **19 من 19**.
- **نتيجة آخر اختبار شامل:** `python tools/test_samples.py` أعطى **ALL OK**، أي 17 من 17 مثالًا نجحت:

| اللغة | الأمثلة المختبرة | المترجم |
|---|---|---|
| Python | 01 و 02 و 03 و 04 و 06 (05 رسومي فاستُبعد) | python 3.13 |
| C | 01 و 02 و 03 | gcc |
| C# | 01 و 02 و 03 | csc .NET 4.0.30319 |
| Java | 01 و 02 و 03 | JDK 25 |
| JavaScript | 01 و 02 و 03 | node |

## 2. آخر ما تم عمله (بالترتيب الزمني)

1. **v1.0:** نقل PWCT إلى Python/Tkinter، مع 67 مكوّنًا لبايثون و 6 أمثلة.
2. **إكمال أوامر الـ Code Mask:** TOFILE/ENDFILE، و ADDVAR/SETVAR، و MERGENEXTTOPREVBYSPACEORSTAR، ومتغيرات `<T_...>` مع Automatic Matching.
3. **v1.1، لغات متعددة:** C و C# و Java و JavaScript، والبناء والتشغيل بالمترجمات الحقيقية، و VPL Compiler بالمترجم، و Programming Languages List.
4. **نقل مكوّني المستخدم** `print` و `printo` من المجلد القديم `components/` إلى `languages/Python/components/`.
5. **التوثيق:**
   - إنشاء `PROJECT_OVERVIEW.md` و `ARCHITECTURE.md` و `CODEBASE_ANALYSIS.md` و `IMPLEMENTATION_PLAN.md` و `CURRENT_STATE.md` و `DECISIONS.md` و `TODO.md`.
   - تحويل `DOCUMENTATION.md` إلى فهرس.
   - إضافة `tools/test_samples.py` و `tools/dbfread.py` إلى المشروع.
6. **v1.2، Form Designer:**
   - `pwct/forms.py` (النموذج) و `pwct/ui/formdesigner.py` (الواجهة)، ويُفتح بزر في الشريط الأيسر أو بـ Ctrl+F أو من قائمة Goal.
   - مكونات الواجهة في Python أعيد بناؤها: صفحة ثانية باسم "Appearance" (عرض، وارتفاع، وخط، ولونان)، وقسم `designer` في كل مكوّن.
   - مكونات جديدة: Text Area و Check Box و List Box، ومكونات Get/Set/Add الخاصة بها. أصبح عدد مكونات Python **75**.
   - تحسين `_insert_index` في المحرك (D38).
   - البحث انتقل إلى Ctrl+Shift+F و F3 (D39).
   - أول اختبارات وحدة: `tests/test_forms.py`.
   - تم التحقق فعليًا: تشغيل نافذة صمّمها المصمم (بكل العناصر والألوان وزر الحدث) انتهى بلا أخطاء.
7. **v1.3، إصلاح "النافذة لا تظهر":**
   - **المشكلة (أبلغ عنها صاحب المشروع):** مكوّن Create Window وحده كان يولّد `tk.Tk()` بلا `mainloop()`، فينتهي البرنامج فورًا (exit code 0) دون أن تظهر النافذة.
   - **الحل (D40):** Create Window أصبح كتلة مثل النافذة في PWCT الأصلي: `Window win1` ← `Start Here` (العناصر) ← `End of Window win1` (فيها `win1.mainloop()`). وخيار جديد في صفحة التفاعل **Show** (مفعّل افتراضيًا).
   - Form Designer: يضيف العناصر الجديدة داخل Start Here، و New Window لم يعد ينشئ Start Event Loop، وخاصية Show في لوحة خصائص النافذة.
   - **ترقية الملفات القديمة تلقائيًا عند الفتح** (`FormModel.upgrade_windows`): النافذة القديمة التي لها Start Event Loop تأخذ Show = 0 (لا يتغير البرنامج)، والتي بلا Event Loop تأخذ Show = 1 وتنتقل عناصرها التالية لها إلى Start Here.
   - مثال `05_GUI_Calculator` أعيد بناؤه بالشكل الجديد، و 4 اختبارات وحدة جديدة.
   - تم التحقق فعليًا: نافذة Create Window وحدها، ومثال الآلة الحاسبة، يبقيان مفتوحين عند التشغيل، وفتح ملف قديم داخل البرنامج يرقّيه ويعمل.
8. **v1.3، Components Browser مثل الأصل (آخر تعديل):**
   - **طلب صاحب المشروع:** ترتيب نافذة المكونات مثل HarbourPWCT (صورة من الأصل).
   - **شجرة مجالات متداخلة لكل اللغات (D41):** الجذر اسم اللغة المرئية (PythonPWCT...) ← User Interface (GUI Application ← Windows و Controls ← Get and Set Values، و Console Application، و Print Text) ← Programming Basics (General و Control Structure و Variables و Data Structures/Arrays و Strings و Operations ← Arithmetic و Files and Folders) ← Programming Paradigm (Structure Programming و OOP) ← System.
   - **شكل الأصل:** عنوان Components Browser، و `ClassicTree` في `common.py` (خطوط منقطة ومربعات +/- مثل TreeView في Windows)، وقائمة المكونات بخط Times New Roman كما في `selser.scx`، و Search أسفلها، و Ok و Close بأيقونته. المجال الذي ليس فيه مكونات يعرض مكونات ما تحته.
   - **التوافق:** `Library.get()` يجد المكوّن باسم ملفه إذا تغيّر مجلده، و `Library.update_keys()` يحدّث المفاتيح عند فتح الملف. تم التحقق: الأمثلة الـ 18 القديمة فُتحت وولّدت نفس الكود بالضبط.
   - **حماية مكونات المستخدم (D42):** `write_components()` لم يعد يحذف مجلد المكونات كله، بل الملفات المسجلة في `_generated.txt` فقط.
   - اختبارات جديدة `tests/test_components.py`، فأصبح المجموع **19 اختبار وحدة**.

## 3. مكان كل شيء

| الشيء | المسار | ملاحظة |
|---|---|---|
| **المشروع (النسخة الرسمية)** | `C:\Users\Win11\Downloads\PyPWCT\` | اعمل هنا |
| **GitHub** | https://github.com/djennad/pwct-in-python-programming-language (الفرع main) | المجلد `Downloads\PyPWCT` هو نسخة git منه: `git add -A` ثم `git commit` ثم `git push`. مكوّنا المستخدم مستثنيان في `.git/info/exclude` |
| نسخة مضغوطة | `C:\Users\Win11\Downloads\PyPWCT.zip` | لا تحتوي مكوّنَي المستخدم |
| السورس الأصلي | `C:\Users\Win11\Downloads\Compressed\doublesvsoop-code-r6075-PWCT Project-First Generation-Environment.zip` | للرجوع إليه عند الحاجة |
| مكونات المستخدم | `languages\Python\components\User Interface\Print Text\print.json` و `printo.json` | ⚠️ لا تحذفها. أدوات `make_*` لم تعد تحذفها (D42) |
| الإعدادات | `%APPDATA%\PyPWCT\settings.json` | حُذفت بعد الاختبارات، فالبرنامج يبدأ بالإعدادات الافتراضية (Python) |
| ملفات التشغيل | `%APPDATA%\PyPWCT\run\` | مؤقتة |

**البيئة على الجهاز:**
- Windows 11، ويعمل بتكبير الشاشة (البرنامج غير DPI-aware).
- Python 3.13 (وفيه Pillow 12، لكنه يُستخدم أثناء التطوير فقط).
- node: `C:\Program Files\nodejs`
- gcc: `Downloads\nim-2.2.10\dist\mingw64\bin`
- clang: LLVM
- JDK 25 (Adoptium)
- dotnet
- csc: `%WINDIR%\Microsoft.NET\Framework64\v4.0.30319`

## 4. الخطوة التالية التي يجب تنفيذها

**المقترح:** إكمال **المرحلة 7: التثبيت والاختبارات**. أُنجز منها `tests/test_forms.py` و `tests/test_components.py` وحماية مكونات المستخدم ومفاتيح المكونات. المتبقي:

> 1. `tests/test_engine.py` و `test_codegen.py` و `test_rules.py`.
> 2. **مكونات جديدة لمجالات الأصل الفارغة** (اختياري): Main Menu و Status Bar و Toolbar و Drawing و Sound و Logic، لتكتمل شجرة المجالات كما في HarbourPWCT.

**تحسينات Form Designer المقترحة** (مفصلة في [TODO](TODO.md)):
- Undo.
- نسخ ولصق العناصر.
- أدوات المحاذاة.
- مصمم قوائم (Menu).
- Form Designer لـ C# (WinForms).

**بديل حسب رغبة صاحب المشروع:** **المرحلة 8** (مكونات Classes و Files للغات الأخرى)، أو **المرحلة 10** (الواجهة العربية).

## 5. أسئلة مفتوحة لصاحب المشروع

1. ما أولويتك التالية: الاختبارات والتثبيت، أم تحسينات Form Designer، أم مكونات أغنى للغات، أم الواجهة العربية؟
2. هل تريد إضافة Harbour، لغة PWCT الأصلية؟ ذلك يتطلب تثبيت مترجم Harbour.
3. هل تريد ملف exe قابلًا للتوزيع؟

## 6. كيف تبدأ جلسة جديدة (بدون إعادة الشرح)

1. أعطِ Claude مسار المشروع `C:\Users\Win11\Downloads\PyPWCT` وقل له: *"اقرأ ملفات التوثيق وابدأ من CURRENT_STATE.md"*.
2. سيشغّل الاختبار أولًا:
   ```
   cd C:\Users\Win11\Downloads\PyPWCT
   python tools/test_samples.py
   ```
3. لتشغيل البرنامج:
   ```
   python PyPWCT.pyw
   ```
4. بعد العمل: تحديث هذا الملف، و [TODO](TODO.md)، و [DECISIONS](DECISIONS.md) إن اتُّخذ قرار جديد.
