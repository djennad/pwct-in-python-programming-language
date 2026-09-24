# CODEBASE_ANALYSIS — تحليل سورس PWCT الأصلي

> جزء من توثيق المشروع:
> [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md) · [ARCHITECTURE](ARCHITECTURE.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [CURRENT_STATE](CURRENT_STATE.md) · [DECISIONS](DECISIONS.md) · [TODO](TODO.md)
>
> **المصدر المدروس:** `C:\Users\Win11\Downloads\Compressed\doublesvsoop-code-r6075-PWCT Project-First Generation-Environment.zip`
> (874 ملفًا، حوالي 6 ميغابايت). من مستودع SourceForge *doublesvsoop*، المراجعة r6075.
> الإصدار: **PWCT 1.9 (Art)**، والنص داخل البرنامج `sys_pwctversion = "PWCT 1.9 (Art) 2025.05.03"`. الرخصة GPL v2 مع استثناء.

---

## 1. التقنيات المستخدمة في الأصل

| الجزء | التقنية |
|---|---|
| البيئة (IDE) | **Visual FoxPro 9**. المشروع `Designers/main.pjx`، والناتج `main.exe` |
| النماذج | ملفات `.scx` و `.sct`: **جدول DBF + ملف memo**. كل صف فيه كائن (`OBJNAME` و `PARENT` و `CLASS`)، مع `PROPERTIES` (النص) و `METHODS` (الكود) |
| الكود | ملفات `.prg` |
| مكتبات الكلاسات | ملفات `.vcx` و `.vct`، مثل `mytool.vcx` (أشرطة الأدوات) و `fdclass.vcx` و `mahvfplib.vcx` |
| القوائم | `.mnx` مع `.mpr` و `sysmenu.prg` |
| البيانات | جداول DBF في `Designers/Data` (`t0` إلى `t48`، و `mydata.dbc`) |
| الشجرة | ActiveX TreeView (`MSCOMCTL.OCX` و `COMCTL32.OCX`) وتُسجَّل عند أول تشغيل بصلاحية Admin |
| مكتبة التشغيل | **SSLib** (DoubleS Library) بلغة Harbour/xHarbour، في `SSLib/SSLIB.PRG` (151 ك.ب) |
| التثبيت | NSIS (`Setup/NewSetup/pwct_NSIS/*.nsh`) و InstallShield (`Setup/PWCT.ise`) |

**طريقة القراءة:** كتبتُ قارئ DBF و FPT صغيرًا بالبايثون (`tools/dbfread.py`) يطبع كل كائن في النموذج مع خصائصه وكوده:
```
python tools/dbfread.py "<path>\Designers\Form\rpwi.scx" form
python tools/dbfread.py "<path>\Designers\Data\t38.dbf" fields
```

## 2. هيكل الأرشيف

```
Designers/                 كود البيئة
  prg/        (39)         الكود: main، cglevel1، cglevel2، goaltores، avoiderrors، stepscolors، ...
  Form/       (168)        النماذج (.scx + .sct)
  Class/      (40)         مكتبات الكلاسات
  Menu/       (14)         القوائم
  Data/       (97)         الجداول
  BMP/        (366)        الصور والأيقونات (منها ما نقلته إلى assets/)
  VPLS/       (23)         تعريفات اللغات: PythonPWCT.txt و CSharpPWCT.txt و CPWCT.txt و SupernovaPWCT.txt + مجلدات Start
  Template/   StartApp/    ملفات البداية (.SSF)
  syslang/                 English و Italian: syslang.txt
  Intellisense/            HarbourPWCT.txt
  config.txt  Style.txt  configbase.txt  syslang.txt  main.pjx/pjt
SSLib/                     مكتبة Harbour (SSLIB.PRG، VSL4.prg، ErrorSys.prg، tcpip.prg، ...)
Setup/                     التثبيت
```

## 3. أهم الملفات والكلاسات والدوال

### 3.1 ملفات الكود (`Designers/prg`)

| الملف | الكلاس / الدوال | الوظيفة | ما يقابله في PyPWCT |
|---|---|---|---|
| `main.prg` | `PWCT_IsAdmin`, `PWCT_GETUSERNAME`, `myquit`, `errHandler` | نقطة البداية: يقرأ المعامل (`.ssf` أو `.trf` أو `.idf` أو `.isf`)، ويحمّل `syslang`، وينشئ الكائنات العامة، ثم `DO FORM welcome/doubles`، ثم `READ EVENTS` | `PyPWCT.pyw` و `mainwindow.main` |
| `cglevel1.prg` | `PWCT_CGLevel1`: `RunTrfScript(form)`, `DeleteStepsNotInScope`, `UpdateCode`, `GetFromListFile`, `PageVarToCodeMaskVar` | **قلب التوليد**: تنفيذ الـ Code Mask وإنشاء الخطوات. الخصائص `lAgain` و `lStepsUpdate` و `lrefreshsteps` | `engine.py` |
| `cglevel2.prg` | `PWCT_CGLevel2`: `Process(code)`, `RemoveTabsAndSpaces`, `TabPushAndTabPop` | أوامر `<pwct:...>` والإزاحة | `codegen.level2` |
| `goaltores.prg` | `arrstree`, `arrdtree`, `findgoals`, `mycodeex`, `mygoalscode`, `ss_arrtree`, `myfastgoalscode`, `myfastcodeex`, `myfastcompress` | ترتيب الشجرة واستخراج الكود بالترتيب (مع `errmap` لربط الأسطر بالخطوات) | `codegen.level1` / `generate` |
| `stepscolors.prg` | `GD_StepsColors`: `setstepcolor`, `determinesteptype`, `checknewstep`, `checksamecolor`, `SaveStyle`, `LoadStyle` | أنواع الخطوات الستة وألوانها، و `Style.txt` | `rules.step_type` + `settings` |
| `avoiderrors.prg` | `GD_AvoidErrors`: `avoidgeneratedsteperrors`, `taskonstepsinthesameinteraction`, `ignorestep`, `deletestep`, `checknewstep`, `isthisstepistheroot`, `checksubcomponent`, `checkparentcomponent`, `isparentallowedforcomponent`, `CheckNewDuplication`, `CheckStepDuplication`, `GetAutoNumber`, `movestepup/down`, `CustomList` | Syntax Directed Editor: أي الأزرار تُفعَّل، والعمليات على كل خطوات التفاعل، والقواعد، ومنع التكرار | `rules.py` + `GoalDesigner._can` |
| `vplrules.prg` | `VPLRulesBase`: `checkAllowRoot`, `CreateMyIndex`, `IndexFind*`, `myfiletostr`, `GETCOMPONENTFILE` | قراءة ملف `.RULES`، وفهارس للسرعة | `components.Component` (القواعد) |
| `vplcompiler.prg` | `GD_VPLCompiler`: `CompileVisualSource`, `CHECKCHILD`, `AddErrorToList`, `deleteOLDInteractions`, `MarkError`, `ShowErrors` | فحص الخطوات: حالة التعطيل، وترتيب `internum`، والتفاعلات القديمة | `VPLCompilerDialog` |
| `timemachine.prg` | `TimeMachineClass.ChangeTime(form)` | إعادة بناء الشجرة حسب قيمة الـ slider | `GoalDesigner.set_frame/refresh` |
| `intellisense.prg` | `IntellisenseClass`: `start`, `LoadIntellisenseData`, `Refresh`, `BuildTree`, `sortlist`, ... | قائمة إكمال في صفحات التفاعل (من `Intellisense/HarbourPWCT.txt`) | `InteractionWindow._intellisense` + `App.program_names` |
| `gui_autonumber.prg` / `gui_autovalue.prg` | `sys_autonumber`, `sys_autovalue` | `<AUTONUMBER>` في القيم الافتراضية (مثل `win1` ثم `win2`) | `engine.expand_default` |
| `nocerror.prg` | (برنامج) | في وضع RPWI يرفض القيم الفارغة | `engine.check_values` |
| `serverbrain.prg` | موزّع أوامر حسب `s_tool`: `CUT`, `COPY`, `PASTE`, `NEW`, `OPEN`, `SAVE`, `K`..`Q`, `S/P/D/F`, `CLOSE` | عمليات الملفات، وتحرير خوادم DoubleS | `App` (new/open/save) |
| `sysmenu.prg` / `menulib.prg` | إجراءات القوائم | القائمة الرئيسية، ونصوصها من `sysmsg(n)` | `App._menu` |
| `runpro.prg` | `PROCESS` (start, waitforexit, kill, ...) | تشغيل البرامج الخارجية | `runner.py` + `subprocess` |
| `doctable.prg` / `sysshots.prg` | `addtodoctable`, `writedoctable` / `area2jpg` | مولّد التوثيق بالصور في Time Machine | ❌ لم يُنقل |
| `mymap.prg` | `startmap`, `domap`, `endmap` | إعادة ترقيم التفاعلات (Order time frames) | `GoalDesigner.order_frames` |
| `fixfolderpath.prg` | `fixfolderpath` | تصحيح مسارات المكونات | — |

### 3.2 النماذج (`Designers/Form`)

| النموذج | الاسم الداخلي | الوظيفة | ما يقابله في PyPWCT |
|---|---|---|---|
| `welcome.scx` | Form1 | شاشة البداية `pwct18logo.png` | `dialogs.Welcome` |
| `DoubleS.scx` | mssf | النافذة الرئيسية: تنشئ `mytool2` و `mytool` (Standard) و `mytool3` (شريط الحالة)، ثم `DO FORM doubles2`، وفيها مؤقت لفتح الملفات المُمرَّرة | `App` |
| `doubles2.scx` | suw | Server Units Window الخاصة بـ DoubleS | ❌ لم يُنقل |
| **`rpwi.scx`** | RPWIFORM | **Goal Designer** | `GoalDesigner` |
| **`selser.scx`** | Form1 | **Components Browser** (Select Component) | `ComponentsBrowser` |
| **`runtrf.scx`** | GALFORM | **Interaction Using Transporter** | `InteractionWindow` |
| `transd.scx` | TRANSDFORM | Transporter Designer: Pages و Code Mask و Matching و Rules | `ComponentDesigner` (التبويبات 2 إلى 4) |
| `interd.scx` | INTERDFORM | Interaction Designer | `ComponentDesigner` (التبويب 1) |
| `stepscolors.scx` | Form1 | Set steps colors، مع 5 أنماط | `StepsColorsDialog` |
| `frmvplcompiler.scx` | Form1 | VPL Compiler | `VPLCompilerDialog` |
| `dtree.scx`، `installpackage`، `newpackage`... | | Domain Tree و Packages | `DomainTreeDialog` (بدون Packages) |
| `searchrpwi.scx` | | البحث في الخطوات | `SearchDialog` |
| `rpwi.Command12` + `selwin.scx` | | **Form Designer**: يجمع خطوات النافذة، ويستخدم الجدول `ld_mymap` لمعرفة المتغير الذي يحمل كل خاصية، ويحدّث التفاعلات. و `selwin` لاختيار النافذة | `pwct/forms.py` + `ui/formdesigner.py` (v1.2) |
| `newgoal`/`editgoal`/`newstep`… | | نوافذ الإدخال | `ask_string` |

**تفاصيل `rpwi.scx`** (المقاس 691×493، و `MDIForm` ومكبّر):
- **الرأس:** `Label1` "Goal Designer"، و `Combo1` (Active Goal)، و `Check3` (Syntax Directed Editor)، وأزرار "Steps Colors" و "VPL Compiler".
- **السطر الثالث:** `Optiongroup2` (Steps Tree / Step Code) بخلفية بنفسجية `64,0,64`، ثم Large/Small steps، ثم Cut و Copy و Paste و Search، ثم `Command16` "The Time Machine"، ثم `slider1`.
- **الشريط الأيسر:** New Step، و Edit، و Delete، و Up، و Down، و **Interact** (`s4_interact.png`)، و **Modify** (`s4_modify.png`)، و Form Designer، و Ignore "X".
- **الأسفل:** Component و Domain و Close.
- **اختصارات `KeyPress`:** رقم 20 (Ctrl+T) Interact، و 13 (Enter) Modify، و 14 (Ctrl+N) New Step، و 6 (Ctrl+F) Form Designer، و 23 (Ctrl+W) Close، و 18 (Ctrl+R) Run. وأي حرف يفتح نافذة المكونات مع البحث (عبر المؤقت `Timer4`).

## 4. جداول البيانات (كما ظهرت في الكود)

| الجدول | المحتوى | الحقول المهمة |
|---|---|---|
| **t33** | الأهداف (Goals) | `goalname`, `goalhandle`, `goaltype` (+ `circuitname`/`branchname`/`resistancename` لـ DoubleS) |
| **t38** | الخطوات | `goalid`, `stepid`, `parentid`, `stepname`, `stepcode`, `stepdis` (معطلة), `stepinterid`, `stepinternum`, `stepdata`/`stepana`/`stepinf`/`stephis` |
| **t46** | سجل التفاعلات (Time Machine) | `f_iid`, `f_stepid`, `f_myhis`, `f_hisdate`, `f_histime` |
| t34 | شجرة المجالات | `childid`, `parentid`, `domainname` |
| t35 | المكونات المثبتة | `servername`, `serverexe` (مسار الملف), `domainid` |
| t42 | عناصر صفحات التفاعل أثناء التشغيل | `rectype`, `o_top`, `o_left`, `o_width`, `o_height`, `o_var`, `o_caption`, `o_options`, `o_trans`, ... |
| t38pic / t34pic | جداول مؤقتة لإعادة ترتيب الشجرة | |

**صيغة سجل التفاعل `f_myhis`** (نص متعدد الأسطر):
- في البداية أسطر عناوين: "[1] Component Name & Path"، و "[2] Component File"، و "[3] Related Variables".
- **السطر 9** = مسار ملف المكوّن `.TRF`، ويُقرأ بـ `MLINE(f_myhis,9)`.
- **من السطر 13 فما بعد**: `[Page] VAR=value` لكل متغير.

## 5. ملفات المكوّن في الأصل

| الملف | الصيغة | المحتوى |
|---|---|---|
| **`.TRF`** (Transporter) | DBF | `f_pages` (أسماء الصفحات)، و `f_files` (ملفات IDF)، و `f_mask` (Code Mask)، و `f_pair1` (متغيرات الصفحات)، و `f_pair2` (متغيرات الـ mask) |
| **`.IDF`** (Interaction) | DBF، سجل لكل عنصر | `rectype`: 0 صفحة (`pcolor` و `pbmp` والمقاس)، 1 Label، 2 TextBox، 3 ListBox (`o_options` سطر لكل عنصر، و `o_trans`: 0 يعني رقم العنصر، وغير 0 يعني نصه)، 4 CheckBox |
| **`.RULES`** | نص | `AllowRoot: n`، و `AllowInteraction: n`، و `AllowParent:`، و `Allow:`، و `Scope:`، و `NoDuplication:`، و `List:` |
| ملف قائمة | نص | قيم الكود المقابلة لعناصر الـ ListBox (`GetFromListFile`)، ويُستخدم مثلًا عندما تكون العناصر المعروضة بالعربية |

قيم خاصة في الصفحات: `<default>` (التركيز على العنصر)، و `<autonumber>`، و `<listboxdefault>`.
متغيرات الـ mask: أي كلمة بالشكل `<...>` أو `[...]` ليست أمرًا. وخوارزمية **Automatic Matching** تحذف `D_` و `TB_` من متغير الصفحة، وتحذف `T_` و `TB_` من متغير الـ mask، ثم تقارن الاسمين.

## 6. كيف يعمل النظام الأصلي

### 6.1 التشغيل
1. `main.prg`: يضبط البيئة، ويقرأ `syslang.txt`. كل نص في الواجهة هو `sysmsg(n)`، أي السطر رقم n في الملف.
2. ينشئ الكائنات العامة: `obj_avoiderrors` و `obj_stepscolors` و `obj_VPLCompiler` و `obj_intellisense`.
3. **وضع RPWI:** إذا وُجد الملف `chpath.txt` فالبرنامج في هذا الوضع (`sys_showdoubles = .F.`)، وإلا يعمل بوضع DoubleS مع ملف `StartApp\Start.SSF`.
4. `DO FORM welcome` أو `doubles`. عند تفعيل `doubles` تُنشأ أشرطة الأدوات، ثم يُفتح `doubles2`.

### 6.2 اختيار اللغة (VPLS)
- `mytool.Combo1.InteractiveChange` ينسخ `VPLS\<Lang>.txt` إلى `chpath.txt` **ويعيد تشغيل `main.exe`**.
- أسطر ملف VPL:
  1. مسار بيانات المكونات، مثل `C:\SSBUILD\RPWIDATA2`
  2. اسم الـ VPL
  3. الامتداد
  4. `build: <bat>`
  5. ملف البداية `.SSF`
- ملف `config.txt` بجانب البرنامج المرئي يحدد `output:` و `build:`. وعند Ctrl+R يُستخرج الكود ويُكتب في ملف الناتج، ثم يُشغَّل `rpwibuild.bat`.

### 6.3 التفاعل (`rpwi.Command5.Click`)
1. التأكد من اختيار Goal، ومن أن الخطوة المختارة ليست `SP_` (الأصل يمنع التفاعل على Start Point).
2. `DO FORM selser` لاختيار المكوّن، ثم `checksubcomponent` للتحقق من القواعد.
3. بناء رأس `myhis`، ثم `DO FORM runtrf WITH file.TRF`.
4. `runtrf.Init`: يقرأ TRF، ثم لكل صفحة `loadpage` تقرأ IDF إلى t42، ثم `pageloaddone` ينشئ العناصر ديناميكيًا داخل scroll container، ثم `showpage`.
5. **Ok** (`closebtn`) أو **Again** (`Command6`) يستدعيان `PWCT_CGLevel1.RunTrfScript(form)`.
6. بعدها تُلوَّن الخطوات الجديدة (`setstepcolor`)، ويُحدَّث Time Machine (`timemachinestartup`).

### 6.4 `RunTrfScript`: الخوارزمية الأصلية
1. `CheckNewDuplication`، ثم تُضاف قيم المتغيرات إلى `t46.f_myhis` بالشكل `VAR=value`.
2. تُستبدل قيم المتغيرات في أسطر `<RPWI:TEST>` فقط، في المصفوفة `tv_error`.
3. حلقة `DO WHILE` تقيّم كتل TEST المتداخلة (VALUE و POSITIVE و NEGATIVE، والبحث بـ `AT()`).
4. تُستبدل القيم في بقية الأسطر، مع `nocerror` لرفض القيم الفارغة.
5. آلة الأوامر: `mymark[30]`، و `NEWSTEP` يضيف عقدة **كابن للعقدة المختارة** ثم يعيد اختيار الأب، و `SETMARK` يختار العقدة المعلَّمة.
6. بعد الانتهاء: `IGNORELAST`، ثم حذف الخطوات غير المستخدمة (`myv_stepuse`)، ثم حذف الخطوات اليتيمة، ثم `PACK`.
7. في Modify (`pv_his`): تُطابق الخطوات القديمة بثلاثة شروط معًا: `stepinternum` و `stepinterid` و `parentid`.

### 6.5 استخراج الكود
`goaltores.myfastgoalscode()`: الخطوات بترتيب الشجرة، مع تجاهل ما فيه `stepdis`، ثم `TabPushAndTabPop`، ثم `PWCT_CGLevel2.Process()`، ثم الكتابة إلى `output`، ثم `rpwibuild.bat`.

### 6.6 بقية الأنظمة
- **Steps Colors:** `determinesteptype` يعطي الأنواع من 1 إلى 6 حسب `stepinterid` و `stepinternum` وقواعد `AllowRoot`/`AllowInteraction` ووجود أبناء. وإذا تساوى لون النص ولون الخلفية تُخفى الخطوة (Read Mode).
- **Syntax Directed:** `avoidgeneratedsteperrors` يفعّل الأزرار أو يعطلها لكل خطوة.
- **Time Machine:** `slider1` + `ChangeTime`، والقائمة في `Command16`: Play as Movie، و Pause، و First/Prev/Next/Last، و Order time frames، و Refresh Steps، و Documentation Generator.
- **VPL Compiler:** `CompileVisualSource` يتحقق من تطابق حالة التعطيل بين خطوات التفاعل الواحد، ومن ترتيب `internum`.

## 7. ملاحظات وأخطاء اكتُشفت في الأصل (وكيف عالجناها)

| الملاحظة في الأصل | المعالجة في PyPWCT |
|---|---|
| عند استبعاد كتلة TEST يفحص الكود المتغير الخطأ (`myvar` بدل `myvar4`)، فلا يُحسب `NEWSTEP` المستبعد ويتغير ترقيم الخطوات | `internum` ثابت = ترتيب السطر في الـ mask (D5) |
| `<pwct:tofile>` يجعل الناتج الرئيسي فارغًا | الملف يُكتب وحده، والكود الرئيسي يبقى (D10) |
| Modify يضيف الخطوة الجديدة في آخر الأبناء | الخطوة تُدرج في مكانها الصحيح (D6) |
| القيمة الفارغة في TEST شبه مستحيلة بسبب المسافة بعد الأمر | التعبير يُقص (D9) |
| الكود قبل `NEWSTEP` يُضاف للخطوة الأب | يُعلَّق حتى الخطوة التالية من نفس التفاعل (D8) |
| لا يمكن التفاعل على Start Point | مسموح (D16) |

أرقام القرارات (D5 وغيرها) مشروحة في [DECISIONS](DECISIONS.md).
