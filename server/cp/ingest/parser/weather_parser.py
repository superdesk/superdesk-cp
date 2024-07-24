# from superdesk.io.feed_parsers.__init__ import FeedParser
# SOURCE = 'Weather Parser' 
# class WeatherParser(FeedParser):
#     label = 'Weather Parser' 
#     NAME = label.lower() # Unique name under which to register the class.

    # def __init__(self):
    #     super().__init__()
#     def can_parse(self, article):
#         # Assuming all files coming from FTP are valid
#         return True
#     def parse(self, article, provider=None):
        
#         item = {}
#         if self.can_parse(article):
#             '''
#             paragraphs = article.split('\n\n')
#             # Extract the slugline and the description
#             first_paragraph = paragraphs[0].split('\n')
#             slugline = first_paragraph[0]
#             description = '\n'.join(first_paragraph[1:])
#             # Isolate the body 
#             body = '\n\n'.join(paragraphs[1:])
#             body = body.replace('\n','\\n') # Adjust for html formatting 
            
#             # Populate item dictionary
#             item['slugline'] = slugline
#             item['description_text'] = description
#             item['body_html'] = f"<p>{body}</p>"
#             item["source"] =  'Environment Canada'
#             '''
#             item['slugline'] = 'Test Slugline1'
#             item['description_text'] =  'Test Description1'
#             item['body_html'] =  'Test Body1'
#             item["source"] =  'Environment Canada1'
#             item["guid"] =  '1234'

#         return item 



class WeatherParser(FeedParser):
    """
    Feed Parser for NINJS format
    """
    
    label = 'Weather Parser'
    
    NAME = label.lower() # Unique name under which to register the class.

    direct_copy_properties = (
        "usageterms",
        "language",
        "headline",
        "copyrightnotice",
        "urgency",
        "pubstatus",
        "mimetype",
        "copyrightholder",
        "ednote",
        "body_text",
        "body_html",
        "slugline",
        "keywords",
        "extra",
        "byline",
        "description_text",
        "profile",
    )

    items = []

    def __init__(self):
        super().__init__()

    def can_parse(self, file_path):
        return True
        # try:
        #     with open(file_path, "r") as f:
        #         ninjs = json.load(f)
        #         if ninjs.get("uri") or ninjs.get("guid"):
        #             return True
        # except Exception as err:
        #     logger.exception(err)
        #     logger.error("Failed to ingest json file")
        #     pass
        # return False

    def parse(self, file_path, provider=None):
        return {
            "guid": "77679c92-b840-4e8e-b601-e40223aa936e",
            "slugline": "Test Slugline 2",
            "body_html" =  'Test Body 2',
            "source" =  "Environment Canada",
            
        }
        

    
