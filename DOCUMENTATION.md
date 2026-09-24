# توثيق PyPWCT — الفهرس

> **في أي جلسة جديدة:** ابدأ بـ [CURRENT_STATE.md](CURRENT_STATE.md)، ثم شغّل `python tools/test_samples.py`.

| الملف | ماذا تجد فيه |
|---|---|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | فكرة المشروع وهدفه، وما أُنجز، وما نريد بناءه، والمسارات، ومسرد المصطلحات |
| [ARCHITECTURE.md](ARCHITECTURE.md) | شجرة الملفات، والطبقات، والكلاسات والدوال الرئيسية، وتواصل الأجزاء، وصيغ الملفات، ونقاط التوسع |
| [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) | تحليل سورس PWCT الأصلي (VFP): الملفات والكلاسات والجداول، وكيف يعمل، والأخطاء المكتشفة فيه |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | منهجية التحويل، والمراحل المنجزة، والمراحل القادمة بالترتيب مع معايير الإنجاز |
| [CURRENT_STATE.md](CURRENT_STATE.md) | أين توقفنا، وآخر تعديل، والخطوة التالية، وأسئلة مفتوحة، وكيف تبدأ جلسة جديدة |
| [DECISIONS.md](DECISIONS.md) | المكتبات والتقنيات المختارة، و 42 قرارًا برمجيًا مع أسبابها |
| [TODO.md](TODO.md) | قائمة المهام المتبقية مرتبة حسب المراحل والأولوية |
| [README.md](README.md) | دليل المستخدم: التشغيل، والاستخدام، والاختصارات، وأوامر الـ Code Mask |

**أدوات المطوّر:**
- `tools/test_samples.py`: الاختبار الشامل.
- `python -m unittest discover -s tests`: اختبارات الوحدة.
- `tools/make_components.py` و `tools/make_samples.py` و `tools/make_languages.py`: توليد المكونات والأمثلة.
- `tools/dbfread.py`: لقراءة نماذج وجداول السورس الأصلي.
