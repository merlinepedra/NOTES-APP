import re
from enum import Enum
from os import path, linesep
from typing import List, AnyStr, Dict

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import TwoLineListItem, MDList, OneLineAvatarIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import BaseSnackbar
from kivymd.uix.textfield import TextInput


from notes_app.utils.observer import Observer

APP_TITLE = "Notes"

SECTION_FILE_SEPARATOR = "<section={name}>"
SECTION_FILE_SEPARATOR_REGEX = "<section=[a-zA-Z]+>"
SECTION_FILE_SEPARATOR_DEFAULT_VALUE = "<section=default>"
SECTION_FILE_NEW_SECTION_PLACEHOLDER = ""
SECTION_FILE_NAME_MINIMAL_CHAR_COUNT = 2

SEARCH_MINIMAL_CHAR_COUNT = 2
SEARCH_LIST_ITEM_POSITION_DISPLAY_VALUE = "Position "
SEARCH_LIST_ITEM_MATCHED_EXTRA_CHAR_COUNT = 30
SEARCH_LIST_ITEM_MATCHED_HIGHLIGHT_COLOR = "ff0000"
SEARCH_LIST_ITEM_MATCHED_HIGHLIGHT_STYLE = "b"


# class Text(TextInput):
#     pass

class ItemDrawer(OneLineAvatarIconListItem):
    icon = StringProperty()
    right_text = StringProperty()
    text = StringProperty()
    delete = ObjectProperty()


class ContentNavigationDrawer(BoxLayout):
    pass


class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        """
        Called when tap on a menu item
        Set the color of the icon and text for the menu item.
        """
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color


class OpenFilePopup(FloatLayout):
    open_file = ObjectProperty(None)
    cancel = ObjectProperty(None)


class ShowFileMetadataPopup(FloatLayout):
    show_file_metadata_label = ObjectProperty(None)
    cancel = ObjectProperty(None)


class ShowAppMetadataPopup(FloatLayout):
    show_app_metadata_label = ObjectProperty(None)
    cancel = ObjectProperty(None)


class AddSectionPopup(FloatLayout):
    add_section_result_message = StringProperty(None)
    execute_add_section = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SearchPopup(FloatLayout):
    search_string_placeholder = StringProperty(None)
    search_results_message = StringProperty(None)
    execute_search = ObjectProperty(None)
    cancel = ObjectProperty(None)


class ScrollableLabel(ScrollView):
    pass


class CustomListItem(TwoLineListItem):
    pass


class CustomSnackbar(BaseSnackbar):
    text = StringProperty(None)
    icon = StringProperty(None)
    font_size = NumericProperty("15sp")


class MenuItems(Enum):
    ChooseFile = "Choose storage file"
    ShowFileInfo = "Show storage file info"
    Save = "Save storage file"
    IncreaseFontSize = "Increase font size"
    DecreaseFontSize = "Decrease font size"
    ShowAppInfo = "Show application info"


class File:
    def __init__(self, file_path, controller):
        self._file_path = file_path
        self._controller = controller
        self._raw_data_content: AnyStr = self.get_raw_data_content()
        self._sections: List[AnyStr] = self.get_sections_from_raw_data_content()
        self._data_by_sections: Dict[AnyStr, AnyStr] = \
            self.transform_raw_data_content_to_data_by_sections()

    def get_raw_data_content(self):
        raw_file_data = self._controller.read_file_data(file_path=self._file_path)
        matches = re.findall(SECTION_FILE_SEPARATOR_REGEX, raw_file_data)

        if not matches:
            raise ValueError("No section in file found")
        return raw_file_data

    def get_sections_from_raw_data_content(self):
        return re.findall(SECTION_FILE_SEPARATOR_REGEX, self._raw_data_content)

    @property
    def default_section(self):
        return self._sections[0]

    @property
    def sections(self):
        return self._sections

    def add_section(self, section_name):
        self._sections.append(section_name)

    def delete_all_sections(self):
        self._sections = []

    def delete_section(self, section_name):
        self._sections.remove(section_name)

    def set_section_content(self, section_name, section_content):
        self._data_by_sections[section_name] = section_content

    def get_section_content(self, section_name):
        return self._data_by_sections[section_name]

    def delete_all_sections_content(self):
        self._data_by_sections = dict()

    def delete_section_content(self, section_name):
        self._data_by_sections.pop(section_name)

    def transform_raw_data_content_to_data_by_sections(self):
        dict_data = dict()
        for item in zip(
                self._sections,
                re.split(SECTION_FILE_SEPARATOR_REGEX, self._raw_data_content)[1:]
        ):
            dict_data[item[0]] = item[1]

        return dict_data

    def transform_data_by_sections_to_raw_data_content(self):
        text_data = str()
        for k, v in self._data_by_sections.items():
            text_data += k
            text_data += v

        return text_data


class MyScreenView(BoxLayout, MDScreen, Observer):
    """"
    A class that implements the visual presentation `MyScreenModel`.

    """
    controller = ObjectProperty()
    model = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.model.add_observer(self)  # register the view as an observer
        self.menu = self.get_menu()
        self.popup = None
        self.last_searched_string = str()

        # self.text_section_view = ???
        self.file = File(
            file_path=None,
            controller=self.controller
        )

        self.filter_data_split_by_section(section_name=self.file.default_section)
        self.set_drawer_items(sections=self.file.sections)

    def filter_data_split_by_section(self, section_name):
        self.text_section_view.section_name = section_name
        self.text_section_view.text = self.file.get_section_content(section_name)
        self.ids.toolbar.title = f"{APP_TITLE} {section_name}"

    def set_drawer_items(self, sections):
        self.ids.md_list.clear_widgets()

        for section_name in sections:
            self.ids.md_list.add_widget(
                ItemDrawer(
                    icon="bookmark",
                    text=section_name,
                    on_release=lambda x=f"{section_name}": self.press_drawer_item_callback(x),
                    delete=self.press_delete_section
                )
            )

    def press_drawer_item_callback(self, text_item):
        self.filter_data_split_by_section(section_name=text_item.text)

    def get_menu(self):
        menu_items = [
            {
                "text": f"{i.value}",
                "viewclass": "OneLineListItem",
                "height": dp(40),
                "on_release": lambda x=f"{i.value}": self.press_menu_item_callback(x),
            } for i in MenuItems
        ]
        return MDDropdownMenu(
            caller=self.ids.toolbar,
            items=menu_items,
            width_mult=5,
        )

    def press_menu_item_callback(self, text_item):
        if text_item == MenuItems.ChooseFile.value:
            self.press_menu_item_open_file()
        elif text_item == MenuItems.ShowFileInfo.value:
            self.press_menu_item_show_file_metadata()
        elif text_item == MenuItems.Save.value:
            self.press_menu_item_save_file()
        elif text_item == MenuItems.IncreaseFontSize.value:
            self.text_section_view.font_size += 1
        elif text_item == MenuItems.DecreaseFontSize.value:
            self.text_section_view.font_size -= 1
        elif text_item == MenuItems.ShowAppInfo.value:
            self.press_menu_item_show_app_metadata()

        self.menu.dismiss()

    def notify_model_is_changed(self):
        """
        The method is called when the model changes.
        Requests and displays the value of the sum.
        """
        snackbar = CustomSnackbar(
            text="success!",
            icon="information",
            snackbar_x="10dp",
            snackbar_y="10dp"
        )
        snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
        snackbar.open()

    def show_error_bar(self, error_message):
        """
        The method is called when the model changes.
        Requests and displays the value of the sum.
        """
        snackbar = CustomSnackbar(
            text=error_message,
            icon="information", # TODO error icon
            snackbar_x="10dp",
            snackbar_y="10dp"
        )
        snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
        snackbar.open()

    def execute_open_file(self, path, filename):
        if not filename:
            return

        file_path = filename[0]
        self.controller.set_file_path(file_path)

        try:
            self.file = File(
                file_path=file_path,
                controller=self.controller
            )
            self.set_drawer_items(self.file.sections)
            self.filter_data_split_by_section(section_name=self.file.default_section)
            self.cancel_popup()

        except ValueError:
            self.file.delete_all_sections()
            self.file.delete_all_sections_content()
            self.cancel_popup()
            self.press_add_section()

    def execute_goto_search_result(self, custom_list_item):
        position = int(custom_list_item.secondary_text.replace(SEARCH_LIST_ITEM_POSITION_DISPLAY_VALUE, ""))
        self.text_section_view.select_text(position, position + len(self.last_searched_string))

        cursor_position = self.text_section_view.get_cursor_from_index(position)
        self.text_section_view.cursor = cursor_position

        self.cancel_popup()

    def execute_search(self, *args):
        if not args[0] or len(args[0]) < SEARCH_MINIMAL_CHAR_COUNT or args[0].isspace():
            self.popup.content.search_results_message = "Invalid search"
            return

        self.last_searched_string = args[0]

        self.popup.content.results_list.clear_widgets()

        text_data = self.text_section_view.text
        found_occurrences = [
            m.start() for m in re.finditer(self.last_searched_string.lower(), text_data.lower())
        ]

        if not found_occurrences:
            self.popup.content.search_results_message = "No match found"
            return

        found_occurrences_count = len(found_occurrences)
        self.popup.content.search_results_message = f"Matches on {found_occurrences_count} positions found" \
            if found_occurrences_count > 1 else f"Match on {found_occurrences_count} position found"

        for position_start in found_occurrences:
            position_end = position_start + len(self.last_searched_string)

            found_string = text_data[position_start:position_end]

            found_string_marked = f"[{SEARCH_LIST_ITEM_MATCHED_HIGHLIGHT_STYLE}]" \
                                  f"[color={SEARCH_LIST_ITEM_MATCHED_HIGHLIGHT_COLOR}]" \
                                  f"{found_string}" \
                                  f"[/color]" \
                                  f"[/{SEARCH_LIST_ITEM_MATCHED_HIGHLIGHT_STYLE}]"

            found_string_extra_chars = \
                text_data[position_end:position_end + SEARCH_LIST_ITEM_MATCHED_EXTRA_CHAR_COUNT]

            self.popup.content.results_list.add_widget(
                CustomListItem(
                    text=f"{found_string_marked}{found_string_extra_chars}...",
                    secondary_text=f"{SEARCH_LIST_ITEM_POSITION_DISPLAY_VALUE}{position_start}",
                    on_release=self.execute_goto_search_result,
                )
            )

    def execute_add_section(self, *args):
        if not args[0] or len(args[0]) < SECTION_FILE_NAME_MINIMAL_CHAR_COUNT or args[0].isspace():
            self.popup.content.add_section_result_message = "Invalid name"
            return

        section_name = args[0]
        section_file_separator = SECTION_FILE_SEPARATOR.format(name=section_name)

        if section_name in self.file.sections:
            self.popup.content.add_section_result_message = "Name already exists"
            return

        self.file.add_section(section_name=section_file_separator)
        self.file.set_section_content(
            section_name=section_file_separator,
            section_content=SECTION_FILE_NEW_SECTION_PLACEHOLDER
        )

        self.filter_data_split_by_section(section_name=section_file_separator)

        self.set_drawer_items(sections=self.file.sections)

        self.cancel_popup()

    def cancel_popup(self):
        self.popup.dismiss()

    def press_menu_item_open_file(self, *args):
        content = OpenFilePopup(open_file=self.execute_open_file,
                                cancel=self.cancel_popup)
        self.popup = Popup(title="Open File", content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def press_menu_item_save_file(self, *args):
        self.file.set_section_content(
            section_name=self.text_section_view.section_name,
            section_content=self.text_section_view.text
        )

        text_data = self.file.transform_data_by_sections_to_raw_data_content()

        self.controller.save_file_data(data=text_data)

    def press_menu_item_show_file_metadata(self, *args):
        content = ShowFileMetadataPopup(
            show_file_metadata_label=self.model.formatted,
            cancel=self.cancel_popup
        )
        self.popup = Popup(title="Show File metadata", content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def press_menu_item_show_app_metadata(self, *args):
        app_info = linesep.join(
            [
                "A simple notes application",
                "- version: TBD",
                "- user can save notes to a local text file",
                "- user can load notes from a local text file",
                "- user can change font size",
                "- user can search in notes"
            ]
        )

        content = ShowAppMetadataPopup(
            show_app_metadata_label=app_info,
            cancel=self.cancel_popup
        )
        self.popup = Popup(title="Show App metadata", content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def press_icon_search(self, *args):
        content = SearchPopup(
            search_string_placeholder=self.last_searched_string,
            search_results_message="",
            execute_search=self.execute_search,
            cancel=self.cancel_popup
        )
        self.popup = Popup(title="Search", content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def press_add_section(self, *args):
        content = AddSectionPopup(
            add_section_result_message="",
            execute_add_section=self.execute_add_section,
            cancel=self.cancel_popup
        )
        self.popup = Popup(title="Add section", content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def press_delete_section(self, section_item):
        if len(self.file.sections) == 1:
            self.show_error_bar(error_message="Cannot delete last section")
            return

        self.ids.md_list.remove_widget(section_item)

        self.filter_data_split_by_section(section_name=self.file.default_section)

        self.file.delete_section(section_name=section_item.text)
        self.file.delete_section_content(section_name=section_item.text)


Builder.load_file(path.join(path.dirname(__file__), "myscreen.kv"))
