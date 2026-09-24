# PROJECT_OVERVIEW — نظرة عامة على مشروع PyPWCT

> جزء من توثيق المشروع. الملفات الأخرى:
> [ARCHITECTURE](ARCHITECTURE.md) · [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [CURRENT_STATE](CURRENT_STATE.md) · [DECISIONS](DECISIONS.md) · [TODO](TODO.md)
>
> آخر تحديث: 2026-09-24، الإصدار **PyPWCT 1.3**.

---

## 1. فكرة المشروع

**PWCT** (Programming Without Coding Technology) لغة برمجة مرئية عامة الأغراض، طوّرها **محمود سمير فايد** بين 2006 و 2025.
بدل كتابة الكود، يتفاعل المبرمج مع **مكونات (Components)**:
1. يختار مكوّنًا، مثل If Statement.
2. يملأ **صفحة تفاعل (Interaction Page)**، مثلًا يكتب الشرط `x > 5`.
3. تتولد **خطوات (Steps)** في **شجرة خطوات (Steps Tree)**، وتحمل كل خطوة جزءًا من الكود الحقيقي.
4. يُستخرج الكود من الشجرة، ثم يُبنى ويُشغَّل.

النسخة الأصلية (الجيل الأول، 1.9 Art) مكتوبة بـ **Visual FoxPro**، ولا تعمل إلا على Windows مع بيئة VFP.
**PyPWCT** إعادة كتابة كاملة لها بـ **Python + Tkinter**، بنفس الشكل ونفس طريقة العمل، مبنية على دراسة السورس الأصلي نفسه.

## 2. الهدف

- **نفس الشكل:** نفس النوافذ والترتيب والأيقونات، مثل Goal Designer و Components Browser و Interaction Using Transporter وغيرها.
- **نفس الوظيفة:** نفس محرك التوليد (أوامر RPWI)، و Syntax Directed Editor، و Time Machine، و Steps Colors، و VPL Compiler.
- **لغات متعددة:** كما في الأصل (HarbourPWCT و PythonPWCT و C#PWCT و CPWCT و SupernovaPWCT)، البيئة واحدة والذي يتغير هو المكونات فقط.
- **بدون تبعيات:** يعمل بمجرد وجود بايثون.
- **قابل للتوسع:** إضافة مكونات ولغات جديدة من داخل البرنامج (Component Designer و Programming Languages List).

## 3. ما تم إنجازه

| المجال | الحالة |
|---|---|
| تحليل السورس الأصلي (VFP): النماذج والكود وصيغ الملفات | ✅ ملخصه في [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) |
| النواة: النموذج، والمحرك (CGLevel1)، ومولّد الكود (CGLevel2)، والقواعد، والمكونات، واللغات | ✅ |
| كل أوامر الـ Code Mask (RPWI و PWCT ومتغيرات `<T_...>` مع Automatic Matching) | ✅ |
| الواجهة: النافذة الرئيسية، و Goal Designer، و Components Browser، ونافذة التفاعل | ✅ |
| Modify، و Again، ونسخ، وقص، ولصق، وتحريك، وتعطيل، وحذف، وبحث، وأكثر من Goal | ✅ |
| Time Machine: إطارات زمنية، وتشغيل كفيلم، وإعادة ترتيب، وتحديث الخطوات | ✅ |
| Steps Colors بأنماطه الخمسة، و Syntax Directed Editor، و VPL Compiler | ✅ |
| Component Designer: Interaction Designer + Transporter Designer + Rules + Test | ✅ |
| Domain Tree: التثبيت، وإلغاء التثبيت، وإنشاء مجالات | ✅ |
| 5 لغات: Python (75 مكوّنًا)، و C (32)، و C# (31)، و Java (31)، و JavaScript (29) | ✅ |
| **Form Designer** (Ctrl+F): تصميم نوافذ Tkinter بالسحب والإفلات، ويحدّث الخطوات نفسها كما في الأصل | ✅ v1.2 (و 1.3: Create Window يُظهر النافذة وحده) |
| البناء والتشغيل بالمترجمات الحقيقية (gcc و csc و java و node) في نافذة Console | ✅ |
| Programming Languages List لإضافة لغة جديدة من داخل البرنامج | ✅ |
| 18 مثالًا: 6 بايثون، و 3 لكل لغة أخرى | ✅ |
| اختبار شامل `tools/test_samples.py`: **17 من 17 نجحت**، مع استبعاد مثال الواجهة الرسومية | ✅ |
| توثيق كامل (هذه الملفات) + `README.md` | ✅ |

ما لم يُنجز بعد موجود بالتفصيل في [TODO](TODO.md) و [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md).

## 4. ما نريد بناءه (الرؤية)

1. **بيئة PWCT كاملة بالبايثون** تغطي كل ما كانت تغطيه النسخة الأصلية، ويبقى من ذلك: Form Designer للغات غير Python، و Packages، ومولّد توثيق Time Machine، وترجمة الواجهة.
2. **مكونات غنية لكل لغة** بمستوى مكونات بايثون: الأصناف، والملفات، والواجهات الرسومية (WinForms و Swing)، والقوائم.
3. **واجهة عربية** اختيارية، مثل ملف `syslang.txt` في الأصل.
4. **لغات إضافية**، مثل Harbour كما في الأصل، و Go و Ruby و PHP.
5. **توزيع سهل**: ملف exe واحد أو برنامج تثبيت، والعمل على Linux و macOS.

## 5. مكان المشروع

| الشيء | المسار |
|---|---|
| المشروع | `C:\Users\Win11\Downloads\PyPWCT\` |
| نسخة مضغوطة | `C:\Users\Win11\Downloads\PyPWCT.zip` |
| السورس الأصلي | `C:\Users\Win11\Downloads\Compressed\doublesvsoop-code-r6075-PWCT Project-First Generation-Environment.zip` |
| إعدادات المستخدم | `%APPDATA%\PyPWCT\settings.json` |
| ملفات التشغيل المؤقتة | `%APPDATA%\PyPWCT\run\` |

**التشغيل:**
```
python PyPWCT.pyw
python PyPWCT.pyw languages\CSharp\samples\02_Guess_The_Number.pwct
```

## 6. مسرد المصطلحات

| المصطلح | المعنى |
|---|---|
| Goal | هدف: شجرة خطوات مستقلة داخل الملف (الملف الواحد قد يحتوي أكثر من هدف) |
| Step | خطوة في الشجرة: مُنشأة يدويًا (تعليق أو تنظيم)، أو مولَّدة من مكوّن (تحمل كودًا) |
| Start Point | جذر الشجرة، وليس خطوة (NOT STEP) |
| Component | مكوّن = صفحات تفاعل + Code Mask + قواعد. في الأصل اسمه Transporter (ملف `.TRF`) |
| Domain / Domain Tree | مجال: مجموعة مكونات. شجرة المجالات تقابل المجلدات |
| Interaction | استخدام واحد لمكوّن مع القيم التي أُدخلت فيه، وهو أيضًا إطار زمني في Time Machine |
| Interaction Page | صفحة إدخال فيها Label و TextBox و ListBox و CheckBox (ملف `.IDF` في الأصل) |
| Code Mask | قالب الكود مع أوامر RPWI، الذي تتولد منه الخطوات |
| Matching | الربط بين متغيرات صفحة التفاعل ومتغيرات الـ Code Mask |
| Modify | إعادة فتح صفحة التفاعل بالقيم القديمة، وتحديث الخطوات دون فقد ما بداخلها |
| internum | رقم الخطوة داخل تفاعلها. الرقم 1 هو الخطوة الجذرية |
| Syntax Directed Editor | منع التعديل اليدوي للخطوات المولَّدة، فلا تتغير إلا بـ Modify |
| VPL | Visual Programming Language، مثل PythonPWCT و C#PWCT |
| RPWI | Real Programming Without codIng: وضع PWCT الذي يولّد كودًا بأي لغة |
| Time Machine | التنقل بين مراحل بناء البرنامج، تفاعلًا بعد تفاعل |
