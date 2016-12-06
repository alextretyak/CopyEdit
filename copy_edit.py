import sublime, sublime_plugin, collections

selection_strings = []

line_endings = {'CR': '\r', 'Unix': '\n', 'Windows': '\r\n'}

#A note about copy_with_empty_selection
#----------------------------------------
#The way the built-in copy works is like this:
#all non-empty sels: copy them
#all empty sels: copy each whole line
#some non-empty sels, some empty: copy only the non-empty
#We're not going to do that, though. If they want to copy empty lines, we'll
#always copy empty lines. I don't understand the copying empty lines in the
#first place, but I would rather be internally consistent.

def print_status_message(verb, numregions=None):
	numregions = numregions or len(selection_strings)
	numchars = sum([len(s[0]) for s in selection_strings])
	message = "{0} {1} character{2}".format(verb, numchars, 's' if numchars != 1 else '')
	if numregions > 1:
		message += " over {0} selection regions".format(numregions)
	sublime.status_message(message)

class CopyEditCommand(sublime_plugin.TextCommand):
	@staticmethod
	def copy(self, edit):
		#See copy_with_empty_selection note above.
		copy_with_empty_sel = self.view.settings().get("copy_with_empty_selection")
		
		new_sel_strings = []
		for s in self.view.sel():
			if len(s):
				new_sel_strings.append((self.view.substr(s), False))
			elif copy_with_empty_sel:
				new_sel_strings.append((self.view.substr(self.view.full_line(s)), True))

		actual_selection_strings = new_sel_strings
		if all(s == new_sel_strings[0] for s in new_sel_strings):
			new_sel_strings = [new_sel_strings[0]]

		if len(new_sel_strings) > 0:
			selection_strings[:] = [] #.clear() doesn't exist in 2.7
			selection_strings.extend(new_sel_strings)
			line_ending = line_endings[self.view.line_endings()]
			sublime.set_clipboard(add_string_to_paste_history(line_ending.join([s[0].replace('\n', line_ending) for s in selection_strings])))
			return actual_selection_strings
		return False
	
	def run(self, edit):
		if self.copy(self, edit):
			print_status_message("Copied")

class CutEditCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		actual_selection_strings = CopyEditCommand.copy(self, edit)
		if actual_selection_strings:
			print_status_message("Cut")
			for s, ss in reversed(list(zip(self.view.sel(), actual_selection_strings))):
				self.view.erase(edit, self.view.full_line(s) if ss[1] else s)

class PasteEditCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		
		#check if clipboard is more up to date
		pasteboard = add_string_to_paste_history(sublime.get_clipboard()) # this is needed when string was copied to clipboard not within Sublime Text
		from_clipboard = False
		if pasteboard != '\n'.join([s[0] for s in selection_strings]):
			selection_strings[:] = [] #.clear() doesn't exist in 2.7
			selection_strings.append((pasteboard, False))
			from_clipboard = True #what should be done in this case?
		
		numstrings = len(selection_strings)
		numsels = len(self.view.sel())
		if numsels == 0:
			return
		
		if numstrings <= numsels and numsels % numstrings == 0:
			strs_per_sel = 1
		elif numsels < numstrings and numstrings % numsels == 0:
			strs_per_sel = int(numstrings / numsels)
		else:
			strs_per_sel = numstrings
		
		str_index = 0
		new_sels = []
		for sel in self.view.sel():
			self.view.erase(edit, sel)
			insertion_point = sel.begin()
			for string in selection_strings[str_index:str_index+strs_per_sel]:
				self.view.insert(edit, self.view.line(insertion_point).begin() if string[1] else insertion_point, string[0])
				insertion_point += len(string[0])
				region = sublime.Region(insertion_point)
				new_sels.append(region)
			str_index = (str_index + strs_per_sel) % numstrings
		
		print_status_message("Pasted", len(self.view.sel()))
		
		self.view.sel().clear()
		for s in new_sels:
			self.view.sel().add(s)

paste_history_deque = collections.deque(maxlen = 15) # 15 is the same as in SublimeText's "Paste from History" list

def add_string_to_paste_history(string):#, do_not_reorder_entries_of_paste_history_deque = False):
	if string == "":
		return
	if string in paste_history_deque:
		paste_history_deque.remove(string)
	paste_history_deque.appendleft(string)
	return string

class PasteFromHistoryIdxCommand(sublime_plugin.TextCommand):
	def run(self, edit, idx):
		if idx != -1:
			sublime.set_clipboard(paste_history_deque[idx])
			self.view.run_command("paste_edit")

class PasteFromHistoryEditCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		add_string_to_paste_history(sublime.get_clipboard()) # this is needed when string was copied to clipboard not within Sublime Text
		if len(paste_history_deque) > 0:
			(self.view.window().show_quick_panel if self.view.settings().get("paste_from_history_quick_panel") else self.view.show_popup_menu)(
				[(s if len(s) < 45 else s[:45] + '...').replace("\n", " ").replace("\t", " ") for s in paste_history_deque],
				lambda idx: self.view.run_command("paste_from_history_idx", {"idx": idx}))

class CopyEditListener(sublime_plugin.EventListener): # for support of standard main menu commands (Edit:Cut/Copy/Paste)
    def on_text_command(self, view, command_name, args):
        if command_name in ["cut", "copy", "paste", "paste_from_history"]: # actually adding "paste_from_history" here does not make any sense because this command is disabled after startup of SublimeText
            return (command_name + "_edit", args)
