# -*- coding: utf-8 -*-

from core.tools.builtin_tool.providers.confluence.common.html2md import ConfluenceHTMLParser
from core.tools.builtin_tool.providers.confluence.confluenceOper import get_page_content
from core.tools.builtin_tool.tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage

from typing import Any, Dict, List, Union

class Convert2mdTool(BuiltinTool):
    def _invoke(self, 
                user_id: str,
               tool_Parameters: Dict[str, Any], 
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        """
            invoke tools
        """

        baseUrl = tool_Parameters['baseUrl']
        pageId = tool_Parameters['pageId']
        username = tool_Parameters['username']
        password = self.runtime.credentials['password']

        wiki_content = get_page_content(baseUrl, username, password, pageId)
        parser = ConfluenceHTMLParser()
        parser.feed(wiki_content)
        markdown_output = parser.get_markdown()

        result = []
        result.append(self.create_file_message(file_name=wiki_content['title'], file_content=markdown_output))

        return result