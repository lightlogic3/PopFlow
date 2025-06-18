import json


class Message:
    """
    A base class for a message. Contains common properties for system, user, and assistant messages.
    """

    def __init__(self, content: str, role: str):
        """
        Initializes the message with the content and the role (system, user, assistant).

        Args:
            content (str): The content of the message.
            role (str): The role of the message sender (system, user, assistant).
        """
        self.content = content
        self.role = role

    def __repr__(self):
        """Return a JSON string when the object is printed or returned."""
        return self.to_dict()

    def to_dict(self) -> dict:
        """Returns the message as a dictionary."""
        return {
            "role": self.role,
            "content": self.content
        }

    def __str__(self):
        return self.__repr__()


class SystemMessage(Message):
    """
    A class representing a system message.
    Inherits from the base Message class.
    """

    def __init__(self, content: str):
        """
        Initializes the system message with the given content.

        Args:
            content (str): The content of the system message.
        """
        super().__init__(content, role="system")


class UserMessage(Message):
    """
    A class representing a user message.
    Inherits from the base Message class.
    """

    def __init__(self, content: str):
        """
        Initializes the user message with the given content.

        Args:
            content (str): The content of the user message.
        """
        super().__init__(content, role="user")


class AssistantMessage(Message):
    """
    A class representing an assistant message.
    Inherits from the base Message class.
    """

    def __init__(self, content: str):
        """
        Initializes the assistant message with the given content.

        Args:
            content (str): The content of the assistant message.
        """
        super().__init__(content, role="assistant")


if __name__ == '__main__':
    print(type((SystemMessage("Hello world").to_dict())))