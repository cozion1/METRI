$path = Join-Path (Get-Location) 'data/seed.json'
$json = Get-Content -Raw $path | ConvertFrom-Json
$skill = $json.skills | Where-Object { $_.id -eq 'HOPE_CORE' }
if (-not $skill) { throw 'HOPE_CORE not found' }
$existingIds = @{}
$skill.scenes | ForEach-Object { $existingIds[$_.id] = $true }
$add = @(
  @{ id='scene_04'; title_he='רעש פנימי'; title_en='Inner Noise'; trait='clarity'; variant='storm_to_signal'; feature='grounding'; hook_sentence='הרעש בפנים גובר, והלב מבקש כיוון.'; panels=@(
      @{id='p1'; text='מחשבות מתנגשות בלי סדר.'},
      @{id='p2'; text='הגוף מרגיש מתוח ולא נינוח.'},
      @{id='p3'; text='אתה מזהה מילה שמובילה את הסערה.'},
      @{id='p4'; text='אתה מניח יד על החזה לנשימה אחת.'},
      @{id='p5'; text='הקצב יורד והצליל מתבהר.'},
      @{id='p6'; text='נולד משפט קצר שמוביל פעולה.'}
    ); choices=@(
      @{id='A'; text='להמשיך להילחם במחשבות'; result='המאבק מגביר את העומס.'},
      @{id='B'; text='לבחור מילה אחת ולנשום איתה'; result='המילה מצמצמת את הרעש.'},
      @{id='C'; text='להסיח את הדעת לגמרי'; result='ההסחה דוחה את ההבנה.'},
      @{id='D'; text='לפרוץ מיד לעשייה גדולה'; result='המהירות מחזירה בלבול.'}
    ); correct_choice_id='B'; reflection='הקלה מתחילה כשמקשיבים למילה אחת.'; task='בחר מילה שמייצגת יציבות וכתוב אותה שלוש פעמים.'; riddle='מה שקט, אך נשמע חזק?'; proverb='שקט פנימי הוא כוח.'; closing='כשיש מילה, יש כיוון.' }
  ,@{ id='scene_05'; title_he='צל של ספק'; title_en='Shadow of Doubt'; trait='courage'; variant='soft_doubt'; feature='reassure'; hook_sentence='הספק לוחש ומבקש תשובה עדינה.'; panels=@(
      @{id='p1'; text='לפני הצעד הבא עולה שאלה קשה.'},
      @{id='p2'; text='הבטן מתכווצת לרגע.'},
      @{id='p3'; text='אתה שם לב שהספק רוצה בטחון.'},
      @{id='p4'; text='אתה כותב תשובה קטנה לעצמך.'},
      @{id='p5'; text='הספק נרגע כשהוא נשמע.'},
      @{id='p6'; text='הצעד הבא כבר פחות מפחיד.'}
    ); choices=@(
      @{id='A'; text='להתעלם מהספק'; result='הספק חוזר חזק יותר.'},
      @{id='B'; text='להוכיח לעצמך בעוצמה'; result='העוצמה מייצרת לחץ.'},
      @{id='C'; text='להקשיב ולנסח תשובה פשוטה'; result='התשובה מקטינה את הפחד.'},
      @{id='D'; text='לבטל את התוכנית'; result='הביטול מוותר על האפשרות.'}
    ); correct_choice_id='C'; reflection='ספק נרגע כשנותנים לו מקום.'; task='כתוב שאלה אחת שמפחידה אותך ותשובה אחת מרגיעה.'; riddle='מה נעלם כשמדברים עליו?'; proverb='לב שומע הוא לב אמיץ.'; closing='הספק הפך לשותף שקט.' }
  ,@{ id='scene_06'; title_he='חלון של הזדמנות'; title_en='Window of Chance'; trait='timing'; variant='brief_opening'; feature='decide'; hook_sentence='הזדמנות קצרה נפתחת בדיוק כשאתה עייף.'; panels=@(
      @{id='p1'; text='הודעה מפתיעה משנה את היום.'},
      @{id='p2'; text='העייפות מנסה לכבות תגובה.'},
      @{id='p3'; text='אתה מזהה שהחלון לא יישאר פתוח.'},
      @{id='p4'; text='אתה בוחר צעד מינימלי עכשיו.'},
      @{id='p5'; text='הגוף מקבל זרם אנרגיה חדש.'},
      @{id='p6'; text='ההזדמנות נשמרת לעוד שלב.'}
    ); choices=@(
      @{id='A'; text='לדחות למחר'; result='החלון נסגר בשקט.'},
      @{id='B'; text='להגיב בצעד מינימלי'; result='הצעד שומר על ההזדמנות.'},
      @{id='C'; text='להגיב מהר מדי'; result='המהירות גורמת לשגיאה.'},
      @{id='D'; text='לא לענות בכלל'; result='הזדמנות חולפת.'}
    ); correct_choice_id='B'; reflection='לפעמים מספיק צעד קטן בזמן.'; task='זהה הזדמנות קטנה היום והגיב בצעד מינימלי.'; riddle='מה פתוח אך לא מחכה?'; proverb='מי שקם בזמן, פוגש מזל.'; closing='החלון נסגר, אבל הכיוון נשאר.' }
  ,@{ id='scene_07'; title_he='עייפות רגשית'; title_en='Emotional Fatigue'; trait='care'; variant='gentle_pause'; feature='rest'; hook_sentence='הרגש מתעייף לפני שהמטרה מושגת.'; panels=@(
      @{id='p1'; text='הגוף כבד והראש איטי.'},
      @{id='p2'; text='האשמה אומרת להמשיך בכוח.'},
      @{id='p3'; text='אתה מזהה צורך במנוחה אמיתית.'},
      @{id='p4'; text='אתה בוחר עצירה מתוכננת.'},
      @{id='p5'; text='הנשימה חוזרת להיות עמוקה.'},
      @{id='p6'; text='הדרך נראית אפשרית מחדש.'}
    ); choices=@(
      @{id='A'; text='להמשיך בלי עצירה'; result='העייפות מצטברת.'},
      @{id='B'; text='לעצור לזמן קצוב ומודע'; result='המנוחה מחזירה כוחות.'},
      @{id='C'; text='לוותר על הכל'; result='הוויתור מגביר ייאוש.'},
      @{id='D'; text='להחליף מטרה'; result='הכיוון מתפזר.'}
    ); correct_choice_id='B'; reflection='מנוחה היא חלק מהתקווה.'; task='קבע 20 דקות מנוחה מודעת בלי מסכים.'; riddle='מה מתקדם כשעוצרים?'; proverb='מנוחה טובה מחזירה כוח.'; closing='מנוחה היום היא תנועה מחר.' }
  ,@{ id='scene_08'; title_he='השוואה כואבת'; title_en='Painful Comparison'; trait='self_acceptance'; variant='quiet_boundaries'; feature='self_view'; hook_sentence='כשאתה משווה, התקווה מתכווצת.'; panels=@(
      @{id='p1'; text='תמונה של מישהו אחר מפעילה לחץ.'},
      @{id='p2'; text='ההישגים שלך נראים קטנים.'},
      @{id='p3'; text='אתה מזהה את ההשוואה כהרגל.'},
      @{id='p4'; text='אתה חוזר לקצב האישי שלך.'},
      @{id='p5'; text='הערכה עצמית מתייצבת.'},
      @{id='p6'; text='המסלול שלך חוזר להיות משמעותי.'}
    ); choices=@(
      @{id='A'; text='להמשיך לגלול ולהשוות'; result='ההשוואה מחלישה.'},
      @{id='B'; text='לסגור את ההשוואה ולרשום הישג אישי'; result='ההישג מחזק זהות.'},
      @{id='C'; text='לבטל את הערך של האחרים'; result='הביטול יוצר מרירות.'},
      @{id='D'; text='להעמיד פנים שהשוואה לא קיימת'; result='הכחשה משאירה כאב.'}
    ); correct_choice_id='B'; reflection='התקווה שלך שייכת לקצב שלך.'; task='כתוב הישג אחד מהשבוע שלא קשור לאף אחד אחר.'; riddle='מה גדל כשמסתכלים פנימה?'; proverb='כל אדם הולך בשביל שלו.'; closing='המסלול שלך הוא הבית שלך.' }
  ,@{ id='scene_09'; title_he='דחייה שקטה'; title_en='Quiet Rejection'; trait='resilience'; variant='bounce_back'; feature='meaning'; hook_sentence='דחייה קטנה מרגישה גדולה כשמצפים.'; panels=@(
      @{id='p1'; text='הודעה קצרה מסיימת אפשרות.'},
      @{id='p2'; text='הגוף מתכווץ לשבריר שנייה.'},
      @{id='p3'; text='אתה מבחין שהסיפור בראש מיד גדל.'},
      @{id='p4'; text='אתה מחזיר את הסיפור לגודל אמיתי.'},
      @{id='p5'; text='הדחייה הופכת לשיעור.'},
      @{id='p6'; text='התקווה מקבלת כיוון חדש.'}
    ); choices=@(
      @{id='A'; text='להסיק שזה אומר עליך הכל'; result='ההכללה פוגעת בביטחון.'},
      @{id='B'; text='לשחרר ולנסח למידה קצרה'; result='הלמידה שומרת תקווה.'},
      @{id='C'; text='להתנקם או להוכיח'; result='האנרגיה מתבזבזת.'},
      @{id='D'; text='להסתגר לגמרי'; result='ההסתגרות מקטינה אפשרויות.'}
    ); correct_choice_id='B'; reflection='דחייה היא מידע, לא זהות.'; task='כתוב מה למדת מהדחייה במשפט אחד.'; riddle='מה נסגר, אך פותח דלת אחרת?'; proverb='סיבוב אחד של דלת אינו סוף הדרך.'; closing='מה שנגמר פינה מקום לניסיון חדש.' }
  ,@{ id='scene_10'; title_he='קול מבקר פנימי'; title_en='Inner Critic'; trait='compassion'; variant='soft_voice'; feature='self_talk'; hook_sentence='הקול המבקר חזק, אבל אפשר לענות לו ברוך.'; panels=@(
      @{id='p1'; text='הביקורת מופיעה מיד אחרי טעות קטנה.'},
      @{id='p2'; text='אתה מרגיש כיווץ בכתפיים.'},
      @{id='p3'; text='אתה שומע את המשפט החוזר.'},
      @{id='p4'; text='אתה מחליף אותו במשפט אמפתי.'},
      @{id='p5'; text='המתח פוחת בהדרגה.'},
      @{id='p6'; text='הפעולה חוזרת להיות אפשרית.'}
    ); choices=@(
      @{id='A'; text='להאמין לביקורת במלואה'; result='האמונה מחלישה.'},
      @{id='B'; text='לענות במשפט תומך'; result='התמיכה מחזירה יציבות.'},
      @{id='C'; text='לצעוק על עצמך'; result='העוצמה מגבירה לחץ.'},
      @{id='D'; text='להתנתק מהרגש'; result='הניתוק מקטין חיבור.'}
    ); correct_choice_id='B'; reflection='הקול הפנימי יכול להיות בן-ברית.'; task='כתוב משפט אחד שהיית אומר לחבר במצב שלך.'; riddle='מה מרפא בלי לגעת?'; proverb='מילה טובה בונה לב.'; closing='תמיכה פנימית מחזירה תנועה.' }
  ,@{ id='scene_11'; title_he='אכזבה חוזרת'; title_en='Recurring Disappointment'; trait='persistence'; variant='steady_return'; feature='recommit'; hook_sentence='אכזבה חוזרת בודקת את הסבלנות שלך.'; panels=@(
      @{id='p1'; text='שוב אותה תחושה של כישלון.'},
      @{id='p2'; text='ההבנה שאתה עדיין כאן.'},
      @{id='p3'; text='אתה בוחן מה אפשר לשנות.'},
      @{id='p4'; text='אתה בוחר לחזור בצעד אחר.'},
      @{id='p5'; text='המסלול מתעדכן בעדינות.'},
      @{id='p6'; text='התקווה נשמרת דרך ההתמדה.'}
    ); choices=@(
      @{id='A'; text='להגדיר את עצמך ככישלון'; result='ההגדרה מקשה.'},
      @{id='B'; text='לחזור עם שינוי קטן'; result='השינוי מייצר סיכוי חדש.'},
      @{id='C'; text='לשנות יעד לחלוטין'; result='השינוי הרדיקלי מבלבל.'},
      @{id='D'; text='לפעול בלי חשיבה'; result='הפעולה המהירה מפספסת דיוק.'}
    ); correct_choice_id='B'; reflection='התמדה חכמה היא שינוי קטן בזמן.'; task='כתוב שינוי קטן שתנסה בפעם הבאה.'; riddle='מה חוזר, אך לא זהה?'; proverb='מים חוצבים בסלע בטיפה אחר טיפה.'; closing='חזרה חכמה מחזקת תקווה.' }
  ,@{ id='scene_12'; title_he='פחד מהצלחה'; title_en='Fear of Success'; trait='ownership'; variant='bright_edge'; feature='accept'; hook_sentence='לפעמים ההצלחה מפחידה יותר מהכישלון.'; panels=@(
      @{id='p1'; text='הדברים מתקרבים להסתדר.'},
      @{id='p2'; text='פתאום עולה חשש מהשלכות.'},
      @{id='p3'; text='אתה מזהה פחד מאחריות.'},
      @{id='p4'; text='אתה מגדיר גבול נעים להצלחה.'},
      @{id='p5'; text='ההצלחה נעשית בטוחה יותר.'},
      @{id='p6'; text='התקווה מתרחבת בלי לחץ.'}
    ); choices=@(
      @{id='A'; text='לסגת כדי לא להסתכן'; result='הנסיגה מצמצמת אפשרות.'},
      @{id='B'; text='להגדיר איך נראית הצלחה בריאה'; result='ההגדרה מחזירה שליטה.'},
      @{id='C'; text='להאיץ כדי לסיים מהר'; result='ההאצה מגדילה לחץ.'},
      @{id='D'; text='להתעלם מהפחד'; result='הפחד נשאר מתחת לפני השטח.'}
    ); correct_choice_id='B'; reflection='אפשר לבחור הצלחה שמרגישה בטוחה.'; task='כתוב מהי הצלחה בריאה עבורך במשפט אחד.'; riddle='מה גדל אך מפחיד כשנוגעים בו?'; proverb='אחריות היא מפתח לשער חדש.'; closing='ההצלחה יכולה להיות רכה.' }
  ,@{ id='scene_13'; title_he='רגע של אמון'; title_en='Moment of Trust'; trait='trust'; variant='open_step'; feature='reach_out'; hook_sentence='אמון קטן יוצר שינוי גדול ביחסים.'; panels=@(
      @{id='p1'; text='אתה מהסס לבקש עזרה.'},
      @{id='p2'; text='הזיכרון של אכזבות קודמות עולה.'},
      @{id='p3'; text='אתה בוחר לבחור אדם אחד.'},
      @{id='p4'; text='אתה שולח בקשה קצרה וברורה.'},
      @{id='p5'; text='התגובה מגיעה באיטיות אך קיימת.'},
      @{id='p6'; text='התקווה נפתחת דרך קשר.'}
    ); choices=@(
      @{id='A'; text='להתכנס לבד'; result='הבדידות מעמיקה.'},
      @{id='B'; text='לפנות בבקשה אחת ברורה'; result='הפנייה יוצרת קשר.'},
      @{id='C'; text='לשלוח מסר ארוך ומעורפל'; result='העמימות מקשה על תגובה.'},
      @{id='D'; text='לבטל את הצורך בעזרה'; result='הביטול מחליש אמון.'}
    ); correct_choice_id='B'; reflection='אמון מתחיל בבקשה קטנה.'; task='בחר אדם אחד ונסח בקשה אחת ברורה.'; riddle='מה גדל כשמחלקים אותו?'; proverb='יד אחת לא בונה גשר.'; closing='בקשה קטנה פתחה דרך חדשה.' }
)

foreach ($scene in $add) {
  if (-not $existingIds.ContainsKey($scene.id)) {
    $skill.scenes += $scene
  }
}

$json | ConvertTo-Json -Depth 6 | Set-Content -Path $path -Encoding UTF8
