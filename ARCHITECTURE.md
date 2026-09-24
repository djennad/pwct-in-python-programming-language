# ARCHITECTURE — بنية برنامج PyPWCT

> جزء من توثيق المشروع:
> [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md) · [CODEBASE_ANALYSIS](CODEBASE_ANALYSIS.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [CURRENT_STATE](CURRENT_STATE.md) · [DECISIONS](DECISIONS.md) · [TODO](TODO.md)

---

## 1. شجرة المشروع

```
PyPWCT/
├── PyPWCT.pyw              نقطة الدخول: main(sys.argv[1:])
├── Run_PyPWCT.bat          تشغيل بـ pythonw أو pyw
├── README.md               دليل المستخدم
├── PROJECT_OVERVIEW.md  ARCHITECTURE.md  CODEBASE_ANALYSIS.md  IMPLEMENTATION_PLAN.md
├── CURRENT_STATE.md  DECISIONS.md  TODO.md  DOCUMENTATION.md (فهرس)
├── pwct/                   الكود
│   ├── __init__.py         VERSION و APP_NAME و APP_TITLE و FILE_EXT
│   ├── model.py            Project / Goal / Step / Interaction
│   ├── engine.py           محرك RPWI (Level 1)
│   ├── codegen.py          استخراج الكود (Level 1 + Level 2)
│   ├── components.py       Component / Domain / Library
│   ├── rules.py            أنواع الخطوات وقواعد التحرير
│   ├── languages.py        لغات البرمجة (VPLS)
│   ├── settings.py         الإعدادات والألوان
│   ├── runner.py           بناء وتشغيل في Console
│   ├── forms.py            نموذج Form Designer (بدون واجهة)
│   └── ui/                 الواجهة (Tkinter)
│       ├── mainwindow.py   App (المحور)
│       ├── goaldesigner.py Goal Designer + Time Machine
│       ├── browser.py      Components Browser
│       ├── interaction.py  نافذة التفاعل + build_page
│       ├── designer.py     Component Designer
│       ├── formdesigner.py Form Designer (تصميم النوافذ) + Select Window
│       ├── dialogs.py      Goal Viewer / Steps Colors / VPL Compiler / About / Welcome / Samples
│       ├── domaintree.py   Domain Tree
│       ├── languagesdlg.py Programming Languages List
│       └── common.py       أدوات الواجهة المشتركة
├── languages/              بيانات كل لغة
│   ├── _order.txt
│   └── <Python|C|CSharp|Java|JavaScript>/
│       ├── language.json
│       ├── components/<Domain>/<Sub Domain>/.../*.json  (+ _order.txt في كل مستوى، و _generated.txt)
│       ├── samples/*.pwct
│       └── start.pwct      (C و C# و Java فقط)
├── assets/*.png            24 صورة من PWCT الأصلي
└── tools/                  أدوات التطوير
    ├── make_components.py  يبني مكونات بايثون
    ├── make_samples.py     يبني أمثلة بايثون
    ├── make_languages.py   يبني مكونات وأمثلة C و C# و Java و JS
    ├── test_samples.py     اختبار شامل لكل اللغات
    └── dbfread.py          قارئ DBF لدراسة السورس الأصلي
tests/                      اختبارات الوحدة (unittest)
    ├── test_forms.py       Form Designer + إدراج الخطوات في Modify
    └── test_components.py  شجرة المجالات + المفاتيح القديمة + حماية مكونات المستخدم
```

## 2. الطبقات

```
            ┌──────────────────────────── ui/ (Tkinter) ─────────────────────────────┐
            │  App (mainwindow) ◄── هو المحور، ويملك كل الكائنات المشتركة            │
            │     ├─ GoalDesigner ── ComponentsBrowser ── InteractionWindow          │
            │     ├─ ComponentDesigner ── PreviewDialog                              │
            │     └─ CodeViewer / VPLCompilerDialog / StepsColors / DomainTree /     │
            │        LanguagesDialog / Samples / About / Welcome                     │
            └───────────────────────────────┬────────────────────────────────────────┘
                                            │
       ┌────────────────────────────────────▼───────────────────────────────────────┐
       │ النواة (لا تعرف شيئًا عن الواجهة، ويمكن استخدامها من سكربت)                │
       │   engine.Generator ──► model (Step, Interaction)                           │
       │   codegen.generate ──► model + languages.Language                          │
       │   rules.Rules      ──► model + components.Library                          │
       │   components.Library / Component   (JSON)                                  │
       │   languages.Languages / Language   (JSON + تنفيذ الأوامر)                   │
       └────────────────────────────────────┬───────────────────────────────────────┘
                                            │
                     languages/*.json · *.pwct · settings.json · runner.py (عملية منفصلة)
```

**مبدأ مهم:** النواة (`model` و `engine` و `codegen` و `components` و `rules` و `languages`) **مستقلة تمامًا عن Tkinter**. سكربتات `tools/` تستخدمها مباشرة لبناء الأمثلة واختبارها.

## 3. المكونات الرئيسية

### 3.1 `model.py`: نموذج البيانات

| الكلاس | الحقول | أهم الدوال |
|---|---|---|
| `Step` | `id`, `name`, `code`, `info`, `disabled`, `interaction_id`, `internum`, `children`, `parent` | `add(child, index)`, `detach()`, `walk()`, `ancestors()`, `generated`, `to_dict/from_dict` |
| `Interaction` | `id`, `component` (المفتاح), `values` (القيم الخام), `parent_step_id`, `goal`, `date`, `time` | `to_dict/from_dict` |
| `Goal` | `name`, `root` (خطوة Start Point) | |
| `Project` | `language`, `next_id`, `goals`, `interactions`, `filename`, `modified` | `new_id()`, `add_goal()`, `find_step()`, `interaction_steps(iid)`, `interaction_root(iid)`, `goal_interactions(goal)`, `purge_interactions()`, `component_use_count()`, `save()`, `Project.load()` |

### 3.2 `engine.py`: محرك التوليد (يقابل `cglevel1.prg`)

```python
Generator(project, library, lang).run(component, raw_values, goal, parent, interaction=None)
    -> (interaction, created_steps)      # interaction=None: تفاعل جديد، وغير ذلك: Modify
```

الخطوات الداخلية بالترتيب:
1. `check_values()`: رفض القيم الفارغة (إلا مع `allow_empty`)، والتحقق حسب `kind` (بايثون بـ `compile`، وغيرها بـ `_balanced`).
2. `resolve_values()`: تحويل القيم الخام إلى قيم للكود وقيم للعرض (`#{var:item}`)، مع تطبيق الـ escape.
3. `_mask_lines()`: قص كل سطر، وترقيم أسطر `NEWSTEP` (هذا الرقم هو `internum`).
4. `evaluate_tests()`: تقييم `TEST`/`ENDTEST` مع `VALUE` و `POSITIVE`/`NEGATIVE`.
5. `substitute()` مع `_mapping()`: استبدال المتغيرات حسب `component.pairs()`، بدون حساسية لحالة الأحرف، والأطول أولًا.
6. آلة الأوامر: `NEWSTEP` و `PUTMARK` و `SETMARK` (حتى 30 علامة) و `SELECTSTEPBYNAME` و `INFORMATION` و `IGNORELAST`/`IGNORELEVEL` و `NEWVAR`/`SETVARVALUE`/`SELECTVAR`/`REPLACEVARSWITHVALUES` و `NOTE`/`<*>`. أي سطر آخر يُعتبر كودًا ويُضاف للخطوة الحالية.
7. في Modify: يُعاد استخدام الخطوة التي لها نفس `internum`، وما لم يعد يُولَّد يُحذف، والخطوة الجديدة تُدرج في مكانها الصحيح (`_insert_index`).

### 3.3 `codegen.py`: استخراج الكود (يقابل `goaltores.prg` و `cglevel2.prg`)

| الدالة | العمل |
|---|---|
| `level1(project, goals, lang)` | مرور pre-order على الشجرة، ويعطي أزواج `(سطر, خطوة)`. الخطوة المعطلة تُتجاهل مع ما تحتها |
| `level2(pairs, files, lang)` | `TABPUSH`/`TABPOP` تتحول إلى إزاحة، والكتلة الفارغة تأخذ `lang.empty_block`. ويعالج `<pwct:newline>` و `ignorelast` و `mergenexttoprev*` و `addvar`/`setvar` و `tofile`/`endfile` |
| `generate(project, goals, header, files, lang, prelude)` | رأس تعليقي + `lang.prelude` + الكود. يعيد `(code, linemap)`، حيث `linemap[i]` هي خطوة السطر `i+1` |
| `check_syntax(code, linemap, files, lang)` | فحص بايثون بـ `compile`، ويعيد `(msg, line, step, file)` |
| `output_path()` / `write_files()` | مسار ملف الناتج، وكتابة الملف الرئيسي وملفات TOFILE |
| `with_files()` | دمج الملفات الإضافية مع الكود الرئيسي للعرض |

### 3.4 `components.py`: المكونات وشجرة المجالات

- `Component`: `name`, `pages`, `mask`, `matching`, `rules`, `key` (المسار النسبي بدون `.json`).
  - `variables()`
  - `mask_tokens()`: يجمع `#{x}` و `<T_...>`.
  - `auto_pairs()`: خوارزمية Automatic Matching الأصلية.
  - `pairs()`
  - `allow_root(n)`, `allow_interaction(n)`, `allowed_under(n)`, `requires_ancestor`
- `Library(root)`: يمسح المجلدات (بأي عمق) ويبني شجرة من `Domain` حسب `_order.txt`، ويوفر `get(key)` و `all()` و `search(text)`.
  - `get(key)`: إذا لم يوجد المفتاح يبحث باسم الملف (`by_file`)، لأن المفاتيح القديمة مثل `GUI (Tkinter)/Create_Window` صارت `User Interface/GUI Application/Windows/Create_Window` (D41).
  - `update_keys(project)`: يكتب المفاتيح الجديدة في التفاعلات، ويُستدعى في `App.set_project`.

### 3.5 `rules.py`: القواعد

`Rules(project, library, syntax_directed)`:
- `step_type(step)`: يعيد نوعًا من 1 إلى 6 للألوان.
- `locked(step)`
- `allow_sub(step)`
- `is_root(step)`
- `component_allowed(component, parent)`: يطبّق القواعد `allow` ثم `requires_ancestor` ثم `requires_step`.

| النوع | الشرط |
|---|---|
| 1 Created | بلا تفاعل |
| 2 Generated | مولَّدة |
| 3 Root | `internum==1` أو ضمن `allow_root` |
| 4 Allow Sub | ضمن `allow_interaction` ولها أبناء |
| 5 Leaf | مولَّدة بلا أبناء |
| 6 Allow Sub & Leaf | ضمن `allow_interaction` وبلا أبناء |

### 3.6 `languages.py`: اللغات

- `Language`: حقول `language.json`، و `components_dir`، و `samples_dir`، و `start_file`، و `is_python`.
  - `placeholders(source, tmpdir)`: يعيد `{file}` و `{exe}` و `{dir}` و `{name}` و `{python}` و `{tmpdir}`.
  - `command(alternatives, values)`: أول بديل يوجد برنامجه. إذا كان البرنامج نفسه متغيرًا مثل `{exe}` فلا يُفحص.
  - `missing_tools()`
- `Languages(root)`: `reload()`, `get(id|name)`, `default()`, `create(id, data)`.
- `split_command()`, `program_exists()`, `error_lines(output, source)`: الأخيرة تستخرج أرقام أسطر الأخطاء من ناتج المترجم.

### 3.6b `forms.py`: نموذج Form Designer (يقابل `ld_mymap` في `rpwi.scx`)

**الفكرة:** النافذة ليست ملفًا منفصلًا، بل **خطوات**:
- النافذة = تفاعل لمكوّن `designer.type == "window"`.
- عناصرها = تفاعلات مكونات لها `designer`، وقيمة الخاصية `window` فيها تساوي اسم النافذة. الربط بالاسم وليس بمكان الخطوة في الشجرة.

- `FormControl(component, values, interaction)`: `get(prop)`, `set(prop, v)`, `geti(prop)`, `has(prop)`, `name`, `is_new`, `changed`, `deleted`.
- `FormModel(project, library, goal, window_interaction, lang)`:
  - `window` و `controls` و `eventloop`.
  - `windows()` و `window_of_step()`: ثابتتان (static).
  - `add(component, x, y)`: اسم فريد تلقائي. و `delete(control)`.
  - `rename_window(name)`: يحدّث العناصر و Event Loop.
  - `validate()`.
  - `apply(generator)`: يعيد `(updated, added, deleted)`.
  - `create_event(button, generator)`: دالة `<name>_click` قبل النافذة.
  - `create_window(...)`: نافذة جديدة (+ Event Loop فقط إذا لم يكن لمكوّن النافذة `container`).
  - `container()` و `controls_place()`: خطوة Start Here للنافذة (`designer.container` = internum)، ومكان العناصر الجديدة.
  - `upgrade_windows(project, library, generator)`: ثابتة، تُستدعى في `App.open_file` لترقية نوافذ ملفات 1.2 (D40).
- **خصائص الـ mapping:** `name`, `window`, `title`, `text`, `x`, `y`, `w`, `h`, `size`, `fg`, `bg`, `command`, `items`, `show`.
- **`container`** (للنافذة فقط): رقم internum للخطوة التي تحوي العناصر (Start Here = 2).
- **الأنواع:** `window`, `eventloop`, `label`, `button`, `textbox`, `textarea`, `checkbox`, `listbox`.

**قواعد `apply()`:**
1. العنصر المعدَّل يُحدَّث عبر Modify.
2. العنصر المحذوف تُحذف كل خطواته.
3. العنصر الجديد يُولَّد، ثم تُنقل خطوته الجذرية إلى **بعد آخر عنصر للنافذة تحت نفس الأب**، أي قبل Event Loop.
4. التحقق يتم كله قبل أي تعديل (`validate()`).

### 3.7 `runner.py`: عملية منفصلة

`python runner.py job.json`، والملف بالشكل `{"cwd", "title", "steps": [{"title": "Build", "cmd": [...]}, {"title": "Run", "cmd": [...]}]}`.
يُشغَّل في Console جديدة (`CREATE_NEW_CONSOLE`). يتوقف إذا فشل البناء، وينتظر Enter في النهاية.

### 3.8 الواجهة (`ui/`)

| الكلاس | الدور |
|---|---|
| `App` (mainwindow) | يملك: `settings`, `languages`, `language`, `library`, `project`, `rules`, `generator`, `gd`. يوفر القوائم وشريط الأدوات و: `set_language` و `change_language` و `start_project` و `open_file` و `save` و `run_program` و `generate_file` و `output_path` و `program_names` (Intellisense) |
| `GoalDesigner` | الشجرة (`refresh`)، والصلاحيات (`_can`)، و `interact` و `run_interaction` و `modify`، والتحرير، والحافظة، والبحث، و Time Machine (`set_frame` و `play_movie` و `order_frames` و `refresh_steps`) |
| `ComponentsBrowser` | شكل `selser.scx`: `ClassicTree` جذرها اسم اللغة المرئية (`root_name`)، وقائمة بخط Times New Roman، و Search. المجال بلا مكونات يعرض مكونات ما تحته. `show()` يعيد المكوّن المختار، أو None |
| `ClassicTree` (common) | شجرة على Canvas بشكل TreeView في Windows: خطوط منقطة ومربعات +/-، و `insert` و `selection_set` و `see` و `item_open`، ولوحة المفاتيح (الأسهم و +/-) |
| `InteractionWindow` | يبني الصفحات بـ `build_page()`، ويستدعي `on_ok(values, again)` التي تعيد True أو False |
| `ComponentDesigner` | أربعة تبويبات: Pages و Code Mask و Matching و Rules، مع `test()` و `PreviewDialog` |
| `CodeViewer` / `VPLCompilerDialog` | عرض الكود / الفحص، و `compiler_check()` للغات غير بايثون |
| `LanguagesDialog` | تعديل `language.json` وإنشاء لغة جديدة مع `starter_components()` |
| `common` | `image()`, `Gradient`, `ToolTip`, `icon_button`, `Dialog` (الأساس لكل النوافذ), `ask_string`, `ScrolledText`, `highlight_python(text, lang)` |

## 4. طريقة تواصل الأجزاء

### 4.1 Interact

```
GoalDesigner.interact(search)
  ├─ _can("interact")                         (rules.allow_sub + time machine)
  ├─ ComponentsBrowser(allowed=lambda c: app.rules.component_allowed(c, parent)).show()
  └─ run_interaction(comp, parent)
       └─ InteractionWindow(comp, project, on_ok, names_provider=app.program_names).show()
            └─ on_ok(values, again)
                 ├─ app.generator.run(comp, values, goal, parent)   → خطوات جديدة في الشجرة
                 ├─ project.modified = True ; app.update_title()
                 └─ GoalDesigner.refresh()                          → rules.step_type لكل خطوة
```

### 4.2 Modify

```
GoalDesigner.modify() → it = project.interaction(step.interaction_id)
                     → comp = app.library.get(it.component)
                     → parent = interaction_root(it.id).parent
                     → run_interaction(comp, parent, it)      (الصفحة تُعبأ بـ it.values)
                          → generator.run(..., interaction=it)
```

### 4.3 التشغيل (Ctrl+R)

```
App.run_program()
  ├─ generate_file() → _check_code() → codegen.generate(lang) + check_syntax (بايثون)
  │                  → codegen.write_files(output_path(), code, files)
  ├─ lang.command(lang.build, placeholders) → خطوة Build (إن وُجدت)
  ├─ lang.command(lang.run,   placeholders) → خطوة Run
  ├─ %APPDATA%\PyPWCT\run\job.json
  └─ subprocess.Popen([python, runner.py, job.json], CREATE_NEW_CONSOLE)
```

### 4.4 تبديل اللغة

```
vpl_combo / قائمة Transporter / فتح ملف .pwct بلغة أخرى
  → App.change_language(name) → ask_save → set_language(lang)
       library = Library(lang.components_dir) ; rules.library ; generator.library/lang
       settings.language = lang.id
  → set_project(start_project())   (start.pwct إن وُجد)
```

### 4.4b Form Designer (Ctrl+F)

```
GoalDesigner.form_designer() → ui.formdesigner.open_form_designer(app)
  ├─ forms.window_of_step(selected)   → النافذة، أو SelectWindowDialog (فتح أو New Window)
  └─ FormDesigner(app, FormModel(...))       ← Toplevel
        render(): عناصر Tkinter حقيقية داخل Frame بحجم النافذة (WYSIWYG) + شريط عنوان مرسوم
        السحب / الحجم / الأسهم / الخصائص → FormControl.set(...)   (لا يتغير المشروع بعد)
        save() → FormModel.apply(app.generator) → Modify / توليد جديد / حذف
               → gd.refresh()   (الخطوات تتحدث في الشجرة)
        event_code(button) → FormModel.create_event → apply → goto_step("Start Here")
```

### 4.5 VPL Compiler

- فحص الخطوات: وجود المكوّن، وتطابق حالة التعطيل بين خطوات التفاعل الواحد، وترتيب `internum`.
- بايثون: `check_syntax`.
- اللغات الأخرى: `compiler_check()` يكتب الكود في مجلد مؤقت، ثم يشغّل `lang.check` (أو `build` إن لم يوجد)، ثم `error_lines()`، ثم `linemap`، فيظهر اسم الخطوة. النقر المزدوج على الخطأ ينفّذ `gd.goto_step`.

## 5. صيغ الملفات

### 5.1 `.pwct`

```json
{"format": "PyPWCT", "version": "1.1", "language": "Python", "next_id": 12,
 "goals": [{"name": "Main", "root": {"id": "SP_1_", "name": "Start Point (NOT STEP)", "children": [
   {"id": "4_", "name": "If x > 0", "code": "if x > 0:\n<RPWI:TABPUSH>\n", "interaction": "3_",
    "internum": 1, "disabled": true, "children": []}]}}],
 "interactions": [{"id": "3_", "component": "Control Structure/If_Statement", "values": {"cond": "x > 0"},
                   "parent": "SP_1_", "goal": "Main", "date": "2026-09-24", "time": "10:00:00"}]}
```

### 5.2 المكوّن (`components/<Domain>/<Name>.json`)

```json
{"name": "...", "description": "...", "order": 0,
 "pages": [{"name": "...", "bgcolor": "#ffffff", "width": 620, "height": 300, "controls": [...]}],
 "mask": "...", "matching": [["var", "<T_VAR>"]],
 "rules": {"allow_root": [1], "allow_interaction": [2], "requires_ancestor": [], "requires_step": [],
           "allow": {"2": ["Define Function"]}},
 "designer": {"type": "button", "props": {"name": "name", "window": "win", "x": "x", "y": "y",
                                          "w": "w", "h": "h", "text": "text", "command": "cmd"}}}
```

خصائص العناصر:
- `type`: `label`، أو `textbox`، أو `listbox`، أو `checkbox`.
- خصائص عامة: `x`, `y`, `w`, `h`, `fg`, `bg`, `font`, `var`, `title`.
- textbox: `text` (يدعم `<autonumber>`), `kind`, `escape`, `allow_empty`, `focus`.
- listbox: `items`, `values`, `selected`, `mode` (`item` أو `index`).
- checkbox: `caption`, `value`.

### 5.3 `language.json`

`name`, `title`, `extension`, `comment`, `indent`, `empty_block`, `prelude`, `build[]`, `run[]`, `check[]`, `keywords`, `syntax` ("python" أو ""), `description`, `start`.

### 5.4 `settings.json` (في `%APPDATA%\PyPWCT`)

`tree_font`, `tree_font_size`, `syntax_directed`, `colors` (الأنواع 1 إلى 6: لون النص ولون الخلفية), `recent`, `last_dir`, `show_welcome`, `language`.

## 6. نقاط التوسع

| تريد | أين |
|---|---|
| مكوّن جديد | Component Designer (Transporter ← Interaction Designer)، أو داخل `tools/make_*.py` |
| عنصر جديد في Form Designer | مكوّن فيه `"designer": {"type": ..., "props": {...}}`، ثم أضف نوع العرض في `FormDesigner.make_widget` إن كان النوع جديدًا |
| Form Designer للغة أخرى | مكونات Window و Controls لتلك اللغة، مع mapping `designer` بنفس الخصائص |
| لغة جديدة | Transporter ← Programming Languages List، أو داخل `tools/make_languages.py` (`LANGS` و `comp()`) |
| أمر RPWI جديد | `engine.Generator.run` (آلة الأوامر)، وأضفه إلى `designer.RPWI_TAGS` |
| أمر `<pwct:...>` جديد | `codegen.level2` |
| قاعدة جديدة | `rules.Rules.component_allowed` + `components.Component` + تبويب Rules في المصمم |
| نافذة جديدة | ابنِها على `common.Dialog`، واستدعها من `App` |
