# To run this tests just put this script file under SublimeText Packages folder
# and in SublimeText Console enter this command:
# sublime.run_command("cut_copy_paste_tests")

import sublime, sublime_plugin, re

class cut_copy_paste_tests_command(sublime_plugin.ApplicationCommand):
    def run(self):
        # These tests are quite human-readable, but not so human-writable (: as it may seems :). But this is intentional, as in
        # case of small typo exception is raised instead of "smart" guessing what you possibly wanted, and running without fail
        # [and may be even improperly showing test as CORRECTly passed whilst it was INcorrectly parsed].
        tests = """\
(1)
1. Select THIS
2. Additionally [multi-] select THIS2 [also (e.g. with Ctrl+mouse)].
3. Copy [to clipboard (e.g. press Ctrl+C)].
4. Set cursor to here -><-,
   and [also (via Ctrl+click)] to here -><-.
5. Paste [from clipboard (e.g. press Ctrl+V)].

[This works correctly in SublimeText by default (and this plugin SHOULD NOT break this behaviour/functionality).]
This is CORRECT result:
4. Set cursor to here ->THIS<-,
   and [also (via Ctrl+click)] to here ->THIS2<-.


(2)
1. Select THIS
2. Additionally select THIS2
3. Cut [to clipboard (e.g. press Ctrl+X)].
4. Paste [from clipboard (e.g. press Ctrl+V)].
5. Paste [again].

[This test was added based on wbond's comment[https://github.com/SublimeTextIssues/Core/issues/1435#issuecomment-258159654 "When performing editing in multiple selections, if the user cuts and then pastes, the obvious functionality it to cut text from each line and then paste the same text back to where the cursor currently is. This allows you to batch edit lines."].
This works correctly in SublimeText by default (and this plugin SHOULD NOT break this behaviour/functionality).]

This is WRONG result:
1. Select THIS
THIS2THIS
THIS2
2. Additionally select THIS
THIS2THIS
THIS2

This is CORRECT result:
1. Select THISTHIS
2. Additionally select THIS2THIS2


(3)
1. Select T-H-
. . . . . .-I-S
2. Copy.
3. Set cursor to here -><-,
   and to here -><-.
4. Paste.

[This does not work correctly in SublimeText by default (issue[https://github.com/SublimeTextIssues/Core/issues/1435]).]

This is WRONG result:
3. Set cursor to here ->T-H-<-,
   and to here ->. . . . . .-I-S<-.

[But SHOULD works correctly after installing this plugin.]

This is CORRECT result:
3. Set cursor to here ->T-H-
. . . . . .-I-S<-,
   and to here ->T-H-
. . . . . .-I-S<-.


(4)
1. Select THIS
2. Additionally select THIS
3. Copy
4. Set cursor to here -><-
5. Paste

[This does not work correctly in SublimeText by default (issue[https://github.com/SublimeTextIssues/Core/issues/1461]).]

This is WRONG result:
4. Set cursor to here ->THIS
THIS<-

This is ALSO WRONG result [observed in CopyEdit up to version 9b68204818258c33889bc923a15f1d83cad8423e]:
4. Set cursor to here ->THISTHIS<-

This is CORRECT result:
4. Set cursor to here ->THIS<-


(4a)
1. Select THIS
2. Additionally select THIS
3. Cut
4. Set cursor to here -><-
5. Paste

This is CORRECT result:
1. Select 
2. Additionally select 
4. Set cursor to here ->THIS<-


(5)
1. Select THIS
2. Additionally select THIS
3. Copy
4. Set cursor to here -><-,
   and to here -><-.
5. Paste

[This works correctly in SublimeText by default (this test was added just to designate particularity of test (4)
and to check that this [(5) test] behaviour should remain working as well).]

This is CORRECT result:
4. Set cursor to here ->THIS<-,
   and to here ->THIS<-.


(6)
1. Set cursor
   to here -><-
2. Copy
3. Set cursor
    to here -><-
4. Paste

This is CORRECT result:
3. Set cursor
   to here -><-
    to here -><-

This is WRONG result:
3. Set cursor
    to here ->   to here -><-
<-


(7)
1. Set cursor
   to here -><-,
   and to here -><-.
2. Copy.
3. Set cursor
    to here -><-,
    and to here -><-.
4. Paste.

[This test was added based on my comment[https://github.com/SublimeTextIssues/Core/issues/1461#issuecomment-258406270 "... multi-caret [multi-line] cut (Ctrl+X) in SublimeText without selection is even more broken $'`"\U0001f615"`' than pasting in multiple selections (#1435) ..."].]

This is WRONG result:
3. Set cursor
   to here -><-,

   and to here -><-.
    to here -><-,
   to here -><-,

   and to here -><-.
    and to here -><-.

This is ALSO WRONG result:
3. Set cursor
    to here ->   to here -><-,
<-,
    and to here ->   and to here -><-.
<-.

This is CORRECT result:
3. Set cursor
   to here -><-,
    to here -><-,
   and to here -><-.
    and to here -><-.


[Nothing interesting here. This following checks are just for completeness.]
(8)
1. Set cursor
   to here -><-
2. Cut
3. Set cursor
    to here -><-
4. Paste

This is CORRECT result:
1. Set cursor
3. Set cursor
   to here -><-
    to here -><-


(9)
1. Set cursor
   to here -><-,
   and to here -><-.
2. Cut.
3. Set cursor
    to here -><-.
4. Paste.

This is CORRECT result:
1. Set cursor
3. Set cursor
   to here -><-,
   and to here -><-.
    to here -><-.


(10)
1. Select THIS.
2. Copy.
3. Character-by-character select THIS.
4. Paste.

This is WRONG result:
3. Character-by-character select THISTHISITHIS.

This is CORRECT result:
3. Character-by-character select THISTHISTHISTHIS.
"""
        pos = 0
        def read_re(rexp):
            nonlocal pos
            r = re.compile(rexp).match(tests, pos) # re.match(rexp, tests[pos:])
            if not r:
                raise "?"
            pos = r.end() # pos += r.end()
            return r.groups()

        def read_list_of_commands():
            nonlocal pos
            commands = []
            while True:
                commands.append(read_re(R"(\d+)\. ([\s\S]+?)\n(?=\d+\.|\n(?! )|$)"))
                if pos == len(tests):
                    break
                if tests[pos] == "\n":
                    pos += 1 # skip \n
                    break
            return commands

        def skip_comments():
            nonlocal pos
            while tests[pos] == '[':
                #read_re(R"\[[^\[\]]+(?:\[[^\]]+\])?[^\]]+\]\n\n?")
                nesting_level = 0
                while True:
                    ch = tests[pos]
                    if ch == "[":
                        nesting_level += 1
                    elif ch == "]":
                        nesting_level -= 1
                        if nesting_level == 0:
                            pos += 1
                            break
                    pos += 1
                    if pos == len(tests):
                        raise 'Unpaired `[`'
                assert(tests[pos] == "\n")
                pos += 1
                if tests[pos] == "\n":
                    pos += 1

        # Create scratch buffer just for testing purposes
        buffer = sublime.active_window().new_file()
        buffer.set_scratch(True)

        while pos < len(tests):
            # Read test id [test number]
            skip_comments()
            test_id = read_re(R"(\(\w+\))\n")[0]

            # Read commands
            commands = read_list_of_commands()

            # Prepare scratch buffer
            buffer.run_command("select_all")
            buffer.run_command("right_delete")
            buffer.run_command("append", { "characters": "".join([c[0] + '. ' + c[1] + "\n" for c in commands]) } ) # "insert" is not working totally correctly here, so "append" is used instead

            # Process commands
            for command in commands:
                cmd = re.sub(R' \[[^]]+]', '', command[1]) # remove comments
                cmd = cmd.rstrip('.')#rstrip('.', 1) # remove ending `.` if present
                if cmd in ["Cut", "Copy", "Paste"]:
                    #buffer.run_command(cmd.lower()) # this does not work, so emulate correct behaviour manually:
                    overrided_command = sublime_plugin.on_text_command(buffer.id(), cmd.lower(), None)
                    buffer.run_command(*overrided_command if overrided_command[0] else (cmd.lower(),))
                    continue
                def where_command_starts(next = 0): # (using this function below is not totally fair, but much easier)
                    return buffer.find("^" + str(int(command[0])+next) + ". ", 0)
                r = re.match(R"Select (T[-\.\s]*?H[-\.\s]*?I[-\.\s]*?S\d*)$", cmd)
                if r:
                    buffer.sel().clear()
                    buffer.sel().add(buffer.find(r.group(1), where_command_starts().b, sublime.LITERAL))
                    continue
                r = re.match(R"Additionally select (THIS\d*)$", cmd)
                if r:
                    buffer.sel().add(buffer.find(r.group(1), where_command_starts().b, sublime.LITERAL))
                    continue
                r = re.match(R"Character-by-character select (THIS)$", cmd)
                if r:
                    buffer.sel().clear()
                    start = buffer.find(r.group(1), where_command_starts().b, sublime.LITERAL).begin()
                    for x in range(len(r.group(1))):
                        buffer.sel().add(sublime.Region(start + x, start + x + 1))
                    continue
                r = re.match(R"Set cursor\s+to here -><-(?:,\s+and to here -><-)?$", cmd)
                if r:
                    buffer.sel().clear()
                    pos_ = where_command_starts().b
                    end_ = where_command_starts(1).a
                    while True:
                        pos_ = buffer.find("-><-", pos_, sublime.LITERAL).a
                        if pos_ == -1 or pos_ > end_:
                            break
                        pos_ += 2
                        buffer.sel().add(sublime.Region(pos_, pos_))
                    continue
                raise "Unknown command"
            obtained_result = buffer.substr(sublime.Region(0, buffer.size()))

            # Read predetermined results
            compared_result_type = None
            while True:
                skip_comments()
                type_of_result = read_re(R"This is (.+) result(?: \[[^\]]+])?:\n")[0]
                rcommands = read_list_of_commands()

                # Compare this result with processed result
                ccommands = list(commands) # create copy of commands
                for c in rcommands: # write rcommands over ccommands
                    assert(ccommands[int(c[0])-1][0] == c[0] and ccommands[int(c[0])-1][1] != c[1])
                    ccommands[int(c[0])-1] = c
                if "".join([c[0] + '. ' + c[1] + "\n" for c in ccommands]) == obtained_result:
                    assert(compared_result_type == None)
                    compared_result_type = type_of_result
                    #break # break is commented out for more accurate correctness testing/checking

                # Check break conditions
                if pos == len(tests):
                    break
                if tests[pos] == "\n":
                    pos += 1 # skip \n
                    break
            print(test_id + ' ' + (compared_result_type if compared_result_type else "INCORRECT"))

        buffer.close()
