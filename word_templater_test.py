import ptb.templater.word_templater

test_file = "הוראות שימוש בטמפלייטר.docx"
city = "אילת"
ptb.templater.word_templater.fill_template(test_file, ".", city)