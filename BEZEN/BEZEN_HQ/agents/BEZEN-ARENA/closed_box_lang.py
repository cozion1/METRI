"""
Interface strings for the closed box, per language.

Only the chrome is translated here — headings, the explanation of what the file
is, the medical notice. Every word of doctrine in the built file is copied from
the movement's own site in that same language and is never touched.

The taglines are not invented: each is the subtitle of that language's own
teaching page on bruno-groening.org.

The Israeli phone contacts appear in the Hebrew build only. Other languages get
the movement's contact page instead, because we have no local representative to
name and inventing one would be worse than omitting it.

These strings should get a native read before wide distribution. They are
ordinary interface text, not translated scripture, but they carry the medical
notice, which has to land correctly in every language.
"""

STRINGS = {
    "he": {
        "dir": "rtl",
        "title": "ברונו גרונינג — שאלות ותשובות",
        "tagline": "עזרה והחלמה בדרך הרוחנית",
        "draft": ("<b>גרסה לבדיקה — טרם אושרה.</b> החומר הועבר לעופר לייבה ולדוב "
                  "לבדיקה ואישור. אין לראות בתוכן שכאן עמדה רשמית של התנועה עד לאישור."),
        "what_h": "מה זה הדף הזה — ומה הוא איננו",
        "what": [
            ("זהו <b>אוסף סגור של נושאים מובנים עם תשובות מובנות.</b> כל טקסט כאן הועתק "
             "מילה במילה מהאתר הרשמי של חוג ידידי ברונו גרונינג, עם קישור לעמוד המקורי. "
             "שום דבר כאן לא נכתב מחדש ולא נוסח מחדש."),
            ("הדף עובד <b>בלי אינטרנט, בלי שרת ובלי עלות.</b> אפשר לשמור אותו, לשלוח אותו "
             "בוואטסאפ או במייל, ולפתוח אותו בכל מחשב או טלפון."),
            "המשמעות המעשית: אפשר לקרוא כאן <b>מאה אחוז ממה שהדף הזה אי פעם יגיד.</b> אין הפתעות.",
            ("<b>סוכן חי הוא דבר אחר לגמרי.</b> סוכן מבין שאלה שנוסחה בדרך שלא צפינו, מנהל "
             "שיחה שנמשכת לאורך כמה תשובות, ומתאים את דבריו לאדם שמולו. הדף הזה לא עושה "
             "אף אחד מהשלושה — הוא מציג את מה שהוכן מראש, ומחפש בטקסט המקורי. "
             "זה ההבדל בין ספר מסודר היטב לבין שיחה."),
        ],
        "q_h": "שאלות שאנשים שואלים",
        "q_hint": "לחיצה על שאלה פותחת את הפרק שעונה עליה.",
        "questions": [
            ("מה זה בעצם ההתכווננות, ואיך עושים אותה?", 4),
            ("התחלתי להתכוונן, והכאב דווקא החמיר. זה נורמלי?", 5),
            ("כמה זמן לוקח עד שמרגישים משהו?", 5),
            ("מה זה הזרם המרפא?", 3),
            ("למה אנשים חולים, לפי ברונו גרונינג?", 1),
            ("אני לא בטוח שאני מאמין בזה. זה עדיין יכול לעזור?", 6),
            ("האם אפשר לעזור לאדם שלא מבקש עזרה?", 6),
            ("איך משנים הרגל של מחשבות שליליות?", 8),
            ("מה הכוונה שהאדם הוא רוח ולא גוף?", 9),
            ("ומה עם טיפול רפואי — צריך להפסיק?", "med"),
        ],
        "qa_h": "נושאי השיטה",
        "search_h": "חיפוש",
        "search_ph": "חיפוש בכל החומר הרשמי…",
        "hits": "קטעים מהחומר הרשמי",
        "empty": "לא נמצא קטע מתאים. נסה מילה אחרת.",
        "vid_h": "מצגות לצפייה",
        "vid_all": "— כל המצגות —",
        "src": "מקור:",
        "contact_h": "לשאול על חוג",
        "contact": ("לשאלות על חוגים, מפגשים וחוגים מרחוק — הכי טוב לדבר עם אחת משתי "
                    "הנציגות הוותיקות. הן יסבירו ויפנו למנחה בעיר שלך."),
        "med": ("הדף אינו רופא ואינו מאבחן. הקבוצה הרפואית-מדעית של התנועה (MWF) מתארת את "
                "השיטה כ<b>תוספת</b> לידע הרפואי הקונבנציונלי או האלטרנטיבי — לא כתחליף לו. "
                "אין להפסיק, לשנות או לדחות טיפול רפואי על סמך מה שכתוב כאן. "
                "במצב חירום רפואי — פנו מיד לעזרה דחופה."),
        "read": "הקראה", "stop": "עצירה", "bcp": "he-IL",
        "read_hint": "אפשר להאזין לכל פרק — גם בלי חיבור לאינטרנט.",
        "credit": "בליווי טכנולוגי של",
    },
    "en": {
        "dir": "ltr",
        "title": "Bruno Gröning — Questions and Answers",
        "tagline": "Help and healing on the spiritual path",
        "draft": ("<b>Draft for review — not yet approved.</b> This material has been sent "
                  "to the Circle of Friends for review. Nothing here should be taken as the "
                  "movement's official position until it is approved."),
        "what_h": "What this page is — and what it is not",
        "what": [
            ("This is a <b>closed set of topics with fixed answers.</b> Every word of text "
             "here is copied verbatim from the official site of the Bruno Gröning Circle of "
             "Friends, with a link to the original page. Nothing has been rewritten or "
             "rephrased."),
            ("The page works <b>with no internet, no server and no cost.</b> Save it, send it "
             "by email or messenger, open it on any computer or phone."),
            ("What that means in practice: you can read <b>100% of what this page will ever "
             "say.</b> There are no surprises."),
            ("<b>A live agent is something else entirely.</b> An agent understands a question "
             "phrased in a way nobody anticipated, holds a conversation across several "
             "answers, and adapts to the person in front of it. This page does none of those "
             "three — it presents what was prepared in advance and searches the original "
             "text. That is the difference between a well-organised book and a conversation."),
        ],
        "q_h": "Questions people ask",
        "q_hint": "Tap a question to open the chapter that answers it.",
        "questions": [
            ("What is the Einstellen, and how do I do it?", 4),
            ("I started, and the pain got worse. Is that normal?", 5),
            ("How long before I feel anything?", 5),
            ("What is the Heilstrom?", 3),
            ("Why do people become ill, according to Bruno Gröning?", 1),
            ("I am not sure I believe this. Can it still help?", 6),
            ("Can you help someone who has not asked for help?", 6),
            ("How do you change a habit of negative thinking?", 8),
            ("What does it mean that a person is spirit, not body?", 9),
            ("And medical treatment — should I stop it?", "med"),
        ],
        "qa_h": "The teaching",
        "search_h": "Search",
        "search_ph": "Search the official material…",
        "hits": "passages from the official material",
        "empty": "No matching passage. Try a different word.",
        "vid_h": "Presentations",
        "vid_all": "— all presentations —",
        "src": "Source:",
        "contact_h": "Contact",
        "contact": ("For questions about community groups, meetings and distance groups, "
                    "contact the Circle of Friends directly:"),
        "med": ("This page is not a doctor and does not diagnose. The movement's own "
                "Medical-Scientific Group (MWF) describes the method as a <b>supplement</b> "
                "to conventional or alternative medical knowledge — not a replacement for it. "
                "Do not stop, change or postpone medical treatment on the basis of anything "
                "written here. In a medical emergency, seek urgent help immediately."),
        "read": "Read aloud", "stop": "Stop", "bcp": "en-US",
        "read_hint": "Each chapter can be listened to — no internet connection needed.",
        "credit": "Technology by",
    },
    "de": {
        "dir": "ltr",
        "title": "Bruno Gröning — Fragen und Antworten",
        "tagline": "Hilfe und Heilung auf geistigem Weg",
        "draft": ("<b>Entwurf zur Prüfung — noch nicht freigegeben.</b> Dieses Material wurde "
                  "dem Freundeskreis zur Prüfung übergeben. Nichts hier ist bis zur Freigabe "
                  "als offizielle Position der Bewegung zu verstehen."),
        "what_h": "Was diese Seite ist — und was sie nicht ist",
        "what": [
            ("Dies ist eine <b>geschlossene Sammlung von Themen mit festen Antworten.</b> "
             "Jeder Text hier ist wörtlich von der offiziellen Seite des Bruno Gröning "
             "Freundeskreises übernommen, mit Link zur Originalseite. Nichts wurde neu "
             "geschrieben oder umformuliert."),
            ("Die Seite funktioniert <b>ohne Internet, ohne Server und ohne Kosten.</b> "
             "Speichern, per E-Mail oder Messenger versenden, auf jedem Gerät öffnen."),
            ("Das heißt praktisch: Sie können hier <b>100 % dessen lesen, was diese Seite je "
             "sagen wird.</b> Es gibt keine Überraschungen."),
            ("<b>Ein lebendiger Agent ist etwas ganz anderes.</b> Ein Agent versteht eine "
             "Frage, die niemand vorhergesehen hat, führt ein Gespräch über mehrere Antworten "
             "hinweg und geht auf den Menschen ein. Diese Seite tut nichts davon — sie zeigt, "
             "was vorbereitet wurde, und durchsucht den Originaltext. Das ist der Unterschied "
             "zwischen einem gut geordneten Buch und einem Gespräch."),
        ],
        "q_h": "Fragen, die Menschen stellen",
        "q_hint": "Eine Frage antippen öffnet das Kapitel, das sie beantwortet.",
        "questions": [
            ("Was ist das Einstellen, und wie mache ich es?", 4),
            ("Ich habe angefangen, und die Schmerzen wurden stärker. Ist das normal?", 5),
            ("Wie lange dauert es, bis man etwas spürt?", 5),
            ("Was ist der Heilstrom?", 3),
            ("Warum werden Menschen nach Bruno Gröning krank?", 1),
            ("Ich bin nicht sicher, ob ich daran glaube. Kann es trotzdem helfen?", 6),
            ("Kann man jemandem helfen, der nicht um Hilfe bittet?", 6),
            ("Wie ändert man die Gewohnheit negativer Gedanken?", 8),
            ("Was heißt es, dass der Mensch Geist ist und nicht Körper?", 9),
            ("Und die ärztliche Behandlung — soll ich sie abbrechen?", "med"),
        ],
        "qa_h": "Die Lehre",
        "search_h": "Suche",
        "search_ph": "Im offiziellen Material suchen…",
        "hits": "Abschnitte aus dem offiziellen Material",
        "empty": "Kein passender Abschnitt. Versuchen Sie ein anderes Wort.",
        "vid_h": "Präsentationen",
        "vid_all": "— alle Präsentationen —",
        "src": "Quelle:",
        "contact_h": "Kontakt",
        "contact": ("Für Fragen zu Gemeinschaftsstunden, Treffen und Ferngruppen wenden Sie "
                    "sich bitte direkt an den Freundeskreis:"),
        "med": ("Diese Seite ist kein Arzt und stellt keine Diagnose. Die Medizinisch-"
                "Wissenschaftliche Fachgruppe (MWF) der Bewegung beschreibt die Lehre als "
                "<b>Ergänzung</b> zum konventionellen oder alternativen medizinischen Wissen — "
                "nicht als Ersatz dafür. Brechen, ändern oder verschieben Sie keine "
                "medizinische Behandlung aufgrund dessen, was hier steht. Im medizinischen "
                "Notfall sofort Hilfe holen."),
        "read": "Vorlesen", "stop": "Stopp", "bcp": "de-DE",
        "read_hint": "Jedes Kapitel kann vorgelesen werden — auch ohne Internetverbindung.",
        "credit": "Technik von",
    },
    "ru": {
        "dir": "ltr",
        "title": "Бруно Грёнинг — вопросы и ответы",
        "tagline": "Помощь и исцеление на духовном пути",
        "draft": ("<b>Черновик на проверку — ещё не утверждён.</b> Материал передан Кругу "
                  "друзей на проверку. До утверждения ничто здесь не следует считать "
                  "официальной позицией движения."),
        "what_h": "Что это за страница — и чем она не является",
        "what": [
            ("Это <b>закрытый набор тем с готовыми ответами.</b> Весь текст скопирован "
             "дословно с официального сайта Круга друзей Бруно Грёнинга, со ссылкой на "
             "исходную страницу. Ничего не переписано и не переформулировано."),
            ("Страница работает <b>без интернета, без сервера и без затрат.</b> Её можно "
             "сохранить, отправить по почте или в мессенджере, открыть на любом устройстве."),
            ("Практический смысл: вы можете прочитать <b>100% того, что эта страница когда-"
             "либо скажет.</b> Никаких неожиданностей."),
            ("<b>Живой агент — это совсем другое.</b> Агент понимает вопрос, заданный "
             "неожиданным образом, ведёт разговор на протяжении нескольких ответов и "
             "подстраивается под человека. Эта страница не делает ничего из этого — она "
             "показывает подготовленное заранее и ищет по исходному тексту. Это разница "
             "между хорошо составленной книгой и разговором."),
        ],
        "q_h": "Вопросы, которые задают",
        "q_hint": "Нажмите на вопрос, чтобы открыть главу с ответом.",
        "questions": [
            ("Что такое Einstellen и как это делать?", 4),
            ("Я начал, а боль усилилась. Это нормально?", 5),
            ("Сколько времени проходит, прежде чем что-то почувствуешь?", 5),
            ("Что такое Heilstrom?", 3),
            ("Почему люди болеют, по Бруно Грёнингу?", 1),
            ("Я не уверен, что верю в это. Может ли это всё равно помочь?", 6),
            ("Можно ли помочь тому, кто не просил о помощи?", 6),
            ("Как изменить привычку негативных мыслей?", 8),
            ("Что значит, что человек — дух, а не тело?", 9),
            ("А лечение у врача — нужно ли его прекращать?", "med"),
        ],
        "qa_h": "Учение",
        "search_h": "Поиск",
        "search_ph": "Поиск по официальным материалам…",
        "hits": "фрагментов из официальных материалов",
        "empty": "Подходящий фрагмент не найден. Попробуйте другое слово.",
        "vid_h": "Презентации",
        "vid_all": "— все презентации —",
        "src": "Источник:",
        "contact_h": "Контакт",
        "contact": ("По вопросам о группах, встречах и дистанционных группах обращайтесь "
                    "напрямую в Круг друзей:"),
        "med": ("Эта страница не врач и не ставит диагнозов. Медицинско-научная группа "
                "движения (MWF) описывает учение как <b>дополнение</b> к обычным или "
                "альтернативным медицинским знаниям, а не как замену им. Не прекращайте, не "
                "меняйте и не откладывайте лечение на основании написанного здесь. При "
                "неотложном состоянии немедленно обратитесь за срочной помощью."),
        "read": "Прочитать вслух", "stop": "Стоп", "bcp": "ru-RU",
        "read_hint": "Каждую главу можно прослушать — интернет не нужен.",
        "credit": "Технология —",
    },
    "ar": {
        "dir": "rtl",
        "title": "برونو غرونينغ — أسئلة وأجوبة",
        "tagline": "المساعدة والشفاء من خلال الطريق الروحي",
        "draft": ("<b>مسودة للمراجعة — لم تُعتمد بعد.</b> أُرسلت هذه المواد إلى حلقة "
                  "الأصدقاء للمراجعة. لا يُعتبر أي شيء هنا موقفاً رسمياً للحركة قبل الاعتماد."),
        "what_h": "ما هذه الصفحة — وما ليست عليه",
        "what": [
            ("هذه <b>مجموعة مغلقة من المواضيع بإجابات ثابتة.</b> كل نص هنا منقول حرفياً من "
             "الموقع الرسمي لحلقة أصدقاء برونو غرونينغ، مع رابط إلى الصفحة الأصلية. لم "
             "يُعَد كتابة أو صياغة أي شيء."),
            ("تعمل الصفحة <b>بدون إنترنت وبدون خادم وبدون تكلفة.</b> يمكن حفظها وإرسالها "
             "بالبريد أو التطبيقات وفتحها على أي جهاز."),
            ("المعنى العملي: يمكنك أن تقرأ هنا <b>مئة بالمئة مما ستقوله هذه الصفحة على "
             "الإطلاق.</b> لا مفاجآت."),
            ("<b>الوكيل الحي شيء مختلف تماماً.</b> الوكيل يفهم سؤالاً صيغ بطريقة غير "
             "متوقعة، ويُجري محادثة عبر عدة إجابات، ويتكيف مع الشخص أمامه. هذه الصفحة لا "
             "تفعل أياً من ذلك — بل تعرض ما أُعِدّ مسبقاً وتبحث في النص الأصلي. هذا هو "
             "الفرق بين كتاب مرتب جيداً وبين محادثة."),
        ],
        "q_h": "أسئلة يطرحها الناس",
        "q_hint": "اضغط على سؤال ليُفتح الفصل الذي يجيب عليه.",
        "questions": [
            ("ما هو الـ Einstellen وكيف أقوم به؟", 4),
            ("بدأت، وازداد الألم. هل هذا طبيعي؟", 5),
            ("كم من الوقت يمر قبل أن أشعر بشيء؟", 5),
            ("ما هو الـ Heilstrom؟", 3),
            ("لماذا يمرض الناس بحسب برونو غرونينغ؟", 1),
            ("لست متأكداً أنني أؤمن بهذا. هل يمكن أن يساعد رغم ذلك؟", 6),
            ("هل يمكن مساعدة شخص لم يطلب المساعدة؟", 6),
            ("كيف تتغير عادة التفكير السلبي؟", 8),
            ("ماذا يعني أن الإنسان روح وليس جسداً؟", 9),
            ("وماذا عن العلاج الطبي — هل أتوقف عنه؟", "med"),
        ],
        "qa_h": "التعاليم",
        "search_h": "بحث",
        "search_ph": "ابحث في المواد الرسمية…",
        "hits": "مقاطع من المواد الرسمية",
        "empty": "لم يُعثر على مقطع مناسب. جرّب كلمة أخرى.",
        "vid_h": "العروض",
        "vid_all": "— كل العروض —",
        "src": "المصدر:",
        "contact_h": "للتواصل",
        "contact": ("للأسئلة عن الحلقات واللقاءات والمجموعات عن بُعد، تواصل مباشرة مع حلقة "
                    "الأصدقاء:"),
        "med": ("هذه الصفحة ليست طبيباً ولا تُشخِّص. المجموعة الطبية العلمية في الحركة (MWF) "
                "تصف الطريقة بأنها <b>إضافة</b> إلى المعرفة الطبية التقليدية أو البديلة — "
                "وليست بديلاً عنها. لا توقف العلاج الطبي ولا تغيّره ولا تؤجّله بناءً على ما "
                "هو مكتوب هنا. في حالة الطوارئ الطبية اطلب المساعدة العاجلة فوراً."),
        "read": "استماع", "stop": "إيقاف", "bcp": "ar-SA",
        "read_hint": "يمكن الاستماع إلى كل فصل — دون الحاجة إلى اتصال بالإنترنت.",
        "credit": "التقنية من",
    },
}

# Where non-Hebrew readers are sent for local groups, since we have no
# representative to name outside Israel.
CONTACT_URL = "https://www.bruno-groening.org"
