# PyPWCT – البرمجة بدون كتابة كود

> **توثيق المطوّرين:** [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md) · [ARCHITECTURE](ARCHITECTURE.md) · [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [CURRENT_STATE](CURRENT_STATE.md) · [DECISIONS](DECISIONS.md) · [TODO](TODO.md). الفهرس في [DOCUMENTATION.md](DOCUMENTATION.md).

إعادة كتابة لبيئة **PWCT 1.9 (Art)** من تطوير محمود سمير فايد، بلغة **Python + Tkinter**، بنفس الشكل ونفس طريقة العمل.
البرنامج الذي تصممه عبارة عن **شجرة خطوات (Steps Tree)**، ويُنشئها البرنامج من خلال **التفاعل مع المكونات (Components)**.
بعد ذلك تُستخرج الخطوات إلى كود حقيقي بلغة البرمجة التي تختارها، ويُبنى ويُشغَّل مباشرة.

## التشغيل

- المتطلبات: Python 3.8 أو أحدث فقط، ولا تحتاج أي مكتبات إضافية (Tkinter تأتي مع بايثون).
- انقر مرتين على `Run_PyPWCT.bat` أو على `PyPWCT.pyw`، أو نفّذ الأمر:

```
python PyPWCT.pyw
python PyPWCT.pyw languages\CSharp\samples\02_Guess_The_Number.pwct
```

## لغات برمجة متعددة (Visual Programming Languages)

كما في PWCT الأصلي (HarbourPWCT و PythonPWCT و C#PWCT و CPWCT …)، البيئة نفسها تعمل مع أي لغة برمجة.
الذي يتغير بين لغة وأخرى هو المكونات فقط، أي صفحات التفاعل و Code Mask.
اختر اللغة من قائمة **Visual Programming Language** في شريط الأدوات، فتتغير شجرة المكونات والكود المولَّد وطريقة التشغيل.

| VPL | اللغة | المكونات | ما تحتاجه للتشغيل |
|---|---|---|---|
| PythonPWCT | Python 3 | 75 | لا شيء |
| CPWCT | C | 32 | gcc أو clang أو tcc |
| C#PWCT | C# | 31 | لا شيء، لأن csc.exe موجود مع Windows |
| JavaPWCT | Java | 31 | JDK 11 أو أحدث |
| JavaScriptPWCT | JavaScript | 29 | Node.js |

- **كل لغة في مجلد مستقل**: `languages/<Lang>/`، وفيه `language.json` (الامتداد، ونوع التعليق، والإزاحة، والمقدمة Prelude، وأوامر Build و Run و Check)، و `components/` (شجرة المجالات الخاصة بها)، و `samples/`، و `start.pwct`، وهو الملف الذي يُفتح عند File ← New، مثل `VPLS\...\Start.SSF` في الأصل.
- **Ctrl+R**: يولّد الكود، ثم يبنيه بمترجم اللغة (إن كانت تحتاج بناء)، ثم يشغّله في نافذة مستقلة.
- **VPL Compiler (F7)**: في غير Python يشغّل مترجم اللغة الحقيقي، ويربط كل خطأ بالخطوة التي سببته.
- **فتح ملف `.pwct` بلغة أخرى** يبدّل اللغة النشطة تلقائيًا.
- **Transporter ← Programming Languages List**: لتعديل إعدادات أي لغة أو **إضافة لغة جديدة**، مثل Ruby أو Go أو PHP. تُنشأ للغة الجديدة المكونات الأولية Comment و Code، ثم تصمم بقية مكوناتها بـ Component Designer.
- **قواعد خاصة بكل لغة**: مثلًا في C و C# و Java لا يُسمح بتعريف دالة (Define Function) إلا داخل خطوة "Functions"، ولا يُسمح بغير الدوال هناك. هذه هي قواعد `requires_step` و `allow` (ALLOW في PWCT).

## طريقة الاستخدام (كما في PWCT)

1. اختر **Start Point**، أو أنشئ خطوة تنظيمية بـ **New Step** (Ctrl+N).
2. اضغط زر **Interact** (Ctrl+T)، أو اكتب أي حرف في شجرة الخطوات، فتفتح **نافذة المكونات (Components Browser)**.
   - مرتبة مثل الأصل: الجذر اسم اللغة (PythonPWCT)، ثم **User Interface** (GUI Application ← Windows و Controls، و Console Application، و Print Text)، ثم **Programming Basics**، ثم **Programming Paradigm**، ثم **System**.
   - اختيار مجال رئيسي يعرض كل مكونات ما تحته، و **Search** يبحث في كل المكونات.
3. اختر المكون، مثل If Statement، ثم املأ صفحة التفاعل واضغط **Ok**. أو اضغط **Again** لتكرار التفاعل مع إبقاء النافذة مفتوحة.
4. تظهر الخطوات في الشجرة. أضف خطوات داخل الخطوات الخضراء (Start Here / Else ...).
5. **Modify** (Enter): يعيد فتح صفحة التفاعل بالقيم السابقة ويعدّل الخطوات، مع الحفاظ على الخطوات الموجودة بداخلها.
6. **Ctrl+R**: توليد الكود وتشغيله. و **F5**: عرض الكود المولَّد (Goal Viewer Window).

## الاختصارات

| المفتاح | الوظيفة |
|---|---|
| Ctrl+T / أي حرف | Interact (فتح نافذة المكونات مع البحث) |
| Enter | Modify للخطوة المولَّدة |
| Ctrl+N / F2 / Del | خطوة جديدة / تعديل الاسم / حذف |
| Ctrl+Up / Ctrl+Down | تحريك الخطوة لأعلى أو لأسفل |
| Ctrl+X / C / V | قص / نسخ / لصق الخطوات |
| Ctrl+F | **Form Designer**: تصميم النوافذ (نفس اختصار الأصل) |
| Ctrl+Shift+F / F3 | البحث في الخطوات |
| Ctrl+R / Ctrl+G / F5 / F7 | تشغيل / توليد ملف الكود / عرض الكود / VPL Compiler |
| Ctrl+S / Ctrl+O / Ctrl+W | حفظ / فتح / إغلاق |
| Ctrl+Space في صفحة التفاعل | Intellisense (أسماء المتغيرات والدوال الموجودة في برنامجك) |

## المزايا المنقولة من PWCT

- **Goal Designer**: شجرة الخطوات، والأزرار الجانبية، وأكثر من Goal في الملف الواحد، وعرضا Steps Tree / Step Code.
- **Syntax Directed Editor**: لا يمكن تعديل الخطوات المولَّدة أو حذفها إلا عن طريق Modify أو من خطوتها الجذرية، ولا يمكن الإضافة إلا في الأماكن المسموح بها.
- **Steps Colors**: الأنماط الخمسة الأصلية (Default, Black & White, Simple Colors, Read Mode, Read & Design Modes).
- **The Time Machine**: التنقل بين الإطارات الزمنية للتفاعلات، وتشغيلها كفيلم، وإعادة ترتيب الإطارات، وتحديث الخطوات من نسخة المكونات الحالية.
- **VPL Compiler**: فحص الخطوات والكود، مع الانتقال إلى الخطوة التي فيها الخطأ.
- **Domain Tree**: شجرة المجالات، وتثبيت المكونات وإلغاء تثبيتها.
- **Interaction Designer + Transporter Designer**: مصمم مرئي لصفحات التفاعل بالسحب والإفلات، ومحرر لـ Code Mask، وصفحات Matching وRules، وزر Test لمعاينة الخطوات والكود.
- **محرك التوليد (RPWI)**: يدعم كل أوامر Code Mask الموجودة في قائمة الزر الأيمن في `transd.scx`. التفاصيل في القسم التالي.
- **75 مكوّن بايثون** في شجرة مجالات مثل HarbourPWCT: المتغيرات، الإدخال والإخراج، الشروط والتكرار، الدوال، الأصناف (OOP)، القوائم والقواميس، النصوص، الرياضيات، الملفات، واجهات Tkinter، النظام. وبجانبها مكونات C و C# و Java و JavaScript.
- **Form Designer** (Ctrl+F): مصمم مرئي لنوافذ Tkinter. التفاصيل في القسم التالي.

## مصمم النوافذ (Form Designer)

يعمل مثل Form Designer في PWCT الأصلي: **النافذة هي نفسها خطوات في الشجرة**، والمصمم يعدّلها ولا يكتب كودًا منفصلًا.

**شكل النافذة في الشجرة (منذ 1.3):** مكوّن Create Window وحده يكفي لتظهر النافذة:
```
Window win1 : My Application        ← tk.Tk() والعنوان والحجم
    Start Here                      ← ضع هنا عناصر النافذة (Label و Button ...)
    End of Window win1              ← win1.mainloop()  (إذا كان خيار Show مفعّلًا)
```
الدوال التي تستدعيها الأزرار توضع **قبل** خطوة النافذة. والملفات القديمة (1.2) تُرقّى تلقائيًا عند فتحها.

1. **الفتح:** اختر خطوة نافذة (Window) أو أي عنصر من عناصرها، ثم اضغط زر Form Designer في الشريط الأيسر أو Ctrl+F.
   - إذا لم تكن الخطوة المختارة نافذة، تظهر قائمة بالنوافذ الموجودة، مع زر **New Window** لإنشاء نافذة جديدة.
2. **التصميم:**
   - أضف العناصر من شريط Controls: Label و Button و Text Box و Text Area و Check Box و List Box.
   - اسحب العنصر لتحريكه، واسحب المربع الأسود لتغيير حجمه، والمربع الأسود في زاوية النافذة لتغيير حجمها.
   - الأسهم تحرّك العنصر بمقدار 1، ومع Shift بمقدار 10. و Delete يحذف العنصر. وخيار Snap يجعل الحركة بخطوات من 5 نقاط.
3. **الخصائص** (اللوحة اليمنى): الاسم، والنص، والموقع، والحجم (يُترك فارغًا للحجم التلقائي)، وحجم الخط، ولون النص، ولون الخلفية.
   - للزر: **On Click**. النقر المزدوج على الزر ينشئ دالة `button1_click` قبل النافذة، ويربطها به، ثم يعرض عليك الانتقال إلى خطواتها.
   - للنافذة: الاسم، والعنوان، والحجم، ولون الخلفية، و **Show** (إظهار النافذة بـ `mainloop` في آخرها). تغيير اسم النافذة يحدّث كل عناصرها تلقائيًا.
4. **الحفظ (Ctrl+S):** يحدّث خطوات العناصر المعدّلة بـ Modify، ويضيف خطوات العناصر الجديدة داخل **Start Here** الخاصة بالنافذة (قبل `mainloop`)، ويحذف خطوات العناصر المحذوفة. وزر **Save and Run** يحفظ ثم يشغّل البرنامج.

العناصر المعروضة في المصمم هي عناصر Tkinter حقيقية، فما تراه هو ما سيظهر عند التشغيل.
كل ما يصممه المصمم يبقى خطوات عادية، يمكن تعديلها بـ Modify، وتظهر في Time Machine.
المصمم متاح حاليًا في PythonPWCT. ويعمل مع أي مكوّن فيه قسم `designer` في ملفه، لذلك يمكن إضافته للغات أخرى لاحقًا.
- **أمثلة جاهزة لكل لغة** في `languages/<Lang>/samples` (Help ← Samples Manager يعرض أمثلة اللغة النشطة).

## أوامر Code Mask

| الأمر | الوظيفة |
|---|---|
| `<RPWI:NEWSTEP> name` | خطوة جديدة، وأسطر الكود التالية تُخزَّن فيها |
| `<RPWI:PUTMARK> n` / `<RPWI:SETMARK> n` | حفظ آخر خطوة كعلامة / جعل الخطوة المعلَّمة أبًا للخطوات التالية |
| `<RPWI:SELECTSTEPBYNAME> name` | اختيار خطوة باسمها لتصبح الأب |
| `<RPWI:TEST>` … `<RPWI:ENDTEST>` | كتلة شرطية |
| `<RPWI:VALUE>` / `<RPWI:POSITIVE>` / `<RPWI:NEGATIVE>` | القيمة المبحوث عنها، ونوع الاختبار |
| `<RPWI:TABPUSH>` / `<RPWI:TABPOP>` | زيادة الإزاحة / إنقاصها (وتُضاف `pass` تلقائيًا للكتلة الفارغة) |
| `<RPWI:NOTE>` / `<*>` | تعليق يُتجاهل |
| `<RPWI:NEWVAR>` `<RPWI:SETVARVALUE>` `<RPWI:SELECTVAR>` `<RPWI:REPLACEVARSWITHVALUES>` | متغيرات مؤقتة يُستبدل فيها `<NAME>` بقيمته |
| `<RPWI:IGNORELAST> c` / `<RPWI:IGNORELEVEL> n` | حذف آخر حرف c من الكود المولَّد (المستوى 1 = خطوات هذا التفاعل، 2 = كل الأبناء) |
| `<RPWI:INFORMATION> text` | معلومات تُحفظ مع الخطوة |
| `<PWCT:TOFILE> name` … `<PWCT:ENDFILE>` | كتابة الأسطر في ملف آخر بجانب الملف المولَّد |
| `<PWCT:ADDVAR> v` / `<PWCT:SETVAR> value` | في النهاية يُستبدل كل ظهور لـ v بالقيمة |
| `<PWCT:MERGENEXTTOPREV>` / `<PWCT:MERGENEXTTOPREVBYSPACEORSTAR>` | دمج السطر التالي مع السابق (الثاني بدون مسافة إذا انتهى السابق بـ `*`) |
| `<PWCT:IGNORELAST> text` / `<PWCT:NEWLINE>` | حذف نص من نهاية السطر السابق / سطر فارغ |
| `#{var}` و `#{var:item}` | متغير صفحة التفاعل، ونص العنصر المعروض في ListBox |
| `<T_NAME>` `<T_INPUT>` `<T_OUTPUT>` `<T_TB_NAME>` `<T_CB_NAME>` `<T_LB_NAME>` | متغيرات Code Mask بأسلوب PWCT. تربطها Automatic Matching بمتغير الصفحة `NAME` (أو `TB_NAME` …)، ويمكن ربطها يدويًا من صفحة Matching |

## أين يوجد كل جزء من الكود الأصلي؟

| PWCT (Visual FoxPro) | PyPWCT |
|---|---|
| `rpwi.scx` (Goal Designer) | `pwct/ui/goaldesigner.py` |
| `selser.scx` (Components Browser) | `pwct/ui/browser.py` |
| `runtrf.scx` (Interaction Using Transporter) | `pwct/ui/interaction.py` |
| `cglevel1.prg` (RPWI statements) | `pwct/engine.py` |
| `cglevel2.prg` + `goaltores.prg` | `pwct/codegen.py` |
| `stepscolors.prg` + `avoiderrors.prg` + `vplrules.prg` | `pwct/rules.py` |
| `interd.scx` + `transd.scx` | `pwct/ui/designer.py` |
| `dtree.scx` + install/uninstall | `pwct/ui/domaintree.py` |
| `frmvplcompiler.scx`, `stepscolors.scx`, `welcome.scx` | `pwct/ui/dialogs.py` |
| `doubles.scx` + `sysmenu.prg` + `mytool.vcx` | `pwct/ui/mainwindow.py` |
| جداول t33 / t38 / t46 (Goals / Steps / Interactions) | `pwct/model.py` (ملف ‎`.pwct` بصيغة JSON) |
| ملفات `.TRF` + `.IDF` + `.RULES` | ملف مكوّن واحد ‎`.json` في `languages/<Lang>/components/` |
| مجلد `VPLS` (`PythonPWCT.txt` …) + قائمة Visual Programming Language | `pwct/languages.py` + `languages/<Lang>/language.json` + `pwct/ui/languagesdlg.py` |

## إعادة بناء المكونات والأمثلة

```
python tools/make_components.py
python tools/make_samples.py
python tools/make_languages.py
```

الأمر الأول يبني مكونات Python، والثاني أمثلتها، والثالث يبني C و C# و Java و JavaScript (المكونات والأمثلة و start.pwct).
انتبه: هذه الأوامر تعيد إنشاء مجلد `components` لكل لغة، فاحفظ نسخة من أي مكوّن صنعته بنفسك قبل تشغيلها.

## ما لم يُنقل

الأجزاء الخاصة بإطار **DoubleS** القديم، وهي Server Units / Atoms / Electrons / Circuits / Vetos، وكذلك Packages ودعم Harbour.
أما Form Designer فمتاح حاليًا للغة Python فقط.
هذه الأجزاء تكون مخفية أصلًا في PWCT 1.9 عند العمل بوضع RPWI.

## الترخيص

PWCT الأصلي مرخص بـ GPL v2 (حقوق النشر 2006-2025 لمحمود سمير فايد)، وهذه النسخة تستخدم صوره وأيقوناته، لذلك تُوزَّع بنفس الرخصة GPL v2.
