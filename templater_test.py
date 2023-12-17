import ptb.templater.templater

test_file = "הוראות שימוש בטמפלייטר.docx"
city = "חריש"
ptb.templater.templater.fill_word_template(test_file, ".", city)

# test_file = "p2.pptx"
# city = "אילת"
# ptb.templater.templater.fill_ppt_template(test_file, ".", city)