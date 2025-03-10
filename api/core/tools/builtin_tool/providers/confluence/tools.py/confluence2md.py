from core.tools.builtin_tool.providers.confluence.common.html2md import ConfluenceHTMLParser
from core.tools.builtin_tool.providers.confluence.common.confluenceOper import get_page_content
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

        base_url = tool_Parameters['baseUrl']
        page_id = tool_Parameters['pageId']
        username = tool_Parameters['userName']
        password = self.runtime.credentials['password']

        if not base_url or not page_id or not username or not password:
            print(f'error: {tool_Parameters}')
            return self.create_text_message('缺少参数 请检查参数是否正确')

        wiki = get_page_content(base_url, username, password, page_id)
        wiki_content = wiki['results']
        wiki_title = wiki['title']
        print(f'success get wiki content: {wiki_title} length: {len(wiki_content)}')
        parser = ConfluenceHTMLParser()
        parser.feed(wiki_content)
        markdown_output = parser.get_markdown()
        print(f'success convert wiki content to markdown: {wiki_title}')
        result = []
        #markdown_output内容保存为markdown 文件
        result.append(self.create_blob_message(blob=markdown_output.encode('utf-8'),
                                                   meta={ 'mime_type': 'text/markdown' },
                                                    save_as=f"{wiki_title}.md"))
        return result