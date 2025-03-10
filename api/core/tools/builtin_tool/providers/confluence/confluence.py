from core.tools.entities.tool_entities import ToolInvokeMessage, ToolProviderType
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError


from typing import Any, Dict

class ConfluenceProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        pass