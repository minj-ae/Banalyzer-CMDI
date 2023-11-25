from idaapi import PluginForm
from PyQt5 import QtWidgets, QtCore, QtGui
import idautils 
import idaapi
import idc
from idautils import Functions
import ida_funcs
import ida_typeinf

sock_func_list = [
    'socket',
    'bind',
    'listen',
    'accept',
    'connect',
    'send',
    'recv',
    'close'
]

class Form(PluginForm):
    def OnCreate(self, form):
        self.parent = self.FormToPyQtWidget(form)
        self.PopulateForm()

    def PopulateForm(self):
        layout = QtWidgets.QVBoxLayout()

        self.result_table = QtWidgets.QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels(['Where', 'Caller Function', 'Vulnerable Function', 'Vulnerable Function\'s Address', 'Arguments', 'Type'])
        layout.addWidget(self.result_table)

        search_button = QtWidgets.QPushButton("Search")
        search_button.clicked.connect(self.search_and_display_results)
        layout.addWidget(search_button)

        self.parent.setLayout(layout)


    def move_to_function(self, item):
        function_name = item.data(QtCore.Qt.UserRole)
        func_ea = idc.get_name_ea_simple(function_name)
        if func_ea != idc.BADADDR:
            idaapi.jumpto(func_ea)
    def check(self, func_name):
        vuln_func_list = [
            'strcpy', 'strncpy', 'strcat', 'strncat', 'sprintf', 'vsprintf', 'gets', 'memcpy', 'memmove', 'fread',
            'strcpyA', 'strcpyW', 'wcscpy', 'StrCpy', 'lstrcpy', 'lstrcpyA', 'lstrcpyW', 'StrCpyA', 'StrCpyW',
            'lstrcpyn', 'lstrcpynA', 'lstrcpynW', 'StrCpyNW', 'StrCpyNA', 'StrNCpy', 'strncpyA', 'strncpyW', 'wcsncpy',
            'StrCpyN', 'strcatA', 'strcatW', 'lstrcat', 'lstrcatA', 'lstrcatW', 'StrCat', 'StrCatA', 'StrCatW',
            'StrCatBuff', 'StrCatBuffA', 'StrCatBuffW', 'StrCatChainW', 'StrCatN', 'StrCatNA', 'StrCatNW',
            'strncatA', 'strncatW', 'wcsncat', 'StrCatN', 'StrCatNA', 'StrCatNW', 'sprintfA', 'sprintfW', 'wsprintf',
            'wsprintfA', 'wsprintfW', 'sprintfW', 'sprintfA', 'swprintf', 'swprintfA', 'swprintfW', 'vswprintf',
            'vswprintfA', 'vswprintfW', 'vsprintfA', 'vsprintfW', 'vsprintf', 'strcpyA', 'strcpyW', 'wcscpy', 'StrCpy',
            'lstrcpy', 'lstrcpyA', 'lstrcpyW', 'StrCpyA', 'StrCpyW', 'lstrcpyn', 'lstrcpynA', 'lstrcpynW', 'StrCpyNW',
            'StrCpyNA', 'StrNCpy', 'strncpyA', 'strncpyW', 'wcsncpy', 'StrCpyN', 'strcatA', 'strcatW', 'lstrcat',
            'lstrcatA', 'lstrcatW', 'StrCat', 'StrCatA', 'StrCatW', 'StrCatBuff', 'StrCatBuffA', 'StrCatBuffW',
            'StrCatChainW', 'StrCatN', 'StrCatNA', 'malloc', 'free', 'read', 'write'
        ]

        vuln_func_list += ['.' + func_name for func_name in vuln_func_list]


        if func_name in vuln_func_list:
            return True
        else:
            return False
        


    def get_user_defined_functions(self):
        udf = []

        for func_ea in idautils.Functions():
            func_name = idc.get_func_name(func_ea)
            if idc.get_segm_name(func_ea) == ".text":
                udf.append(func_name)

        return udf
    
    def get_function_start_address(self, ea):
        if not isinstance(ea, int):
            try:
                ea = int(ea, 16) 
            except ValueError:
                print("Invalid address format")
                return idc.BADADDR

        func = idaapi.get_func(ea)
        if func:
            return func.start_ea
        return idc.BADADDR
    
    def get_function_start_address_by_name(self, function_name):
        func_ea = idaapi.get_name_ea(0, function_name)
        if func_ea != idaapi.BADADDR and idaapi.is_func(idaapi.get_flags(func_ea)):
            return self.get_function_start_address(func_ea)
        else:
            print("Function not found or address invalid")
            return idc.BADADDR

    def get_func_arguments(self, call_address):
        args_addresses = []

        if not isinstance(call_address, int):
            try:
                call_address = int(call_address, 16) 
            except ValueError:
                print("Invalid address format")
                return idc.BADADDR

        func = ida_funcs.get_func(call_address)
        if func:
            frame = idaapi.get_frame(func)
            if frame:
                sp_offset = idc.get_spd(call_address)

                arg_start_offset = 4 
                for i in range(4): 
                    arg_addr = sp_offset + arg_start_offset + (i * 4)

                    if arg_addr < 0:
                        arg_addr = 0xFFFFFFFF + arg_addr + 1  

                    args_addresses.append(hex(arg_addr))

        return args_addresses


    def get_function_name(self, ea):
        if not isinstance(ea, int):
            try:
                ea = int(ea, 16) 
            except ValueError:
                print("Invalid address format")
                return idc.BADADDR

        func = idaapi.get_func(ea)
        if func:
            return func.name
        return idc.BADADDR

    def find_function_xrefs(self, target_function):
        func_ea = idc.get_name_ea_simple(target_function)
        if func_ea != idc.BADADDR:
            func_start_ea = idc.get_func_attr(func_ea, idc.FUNCATTR_START)
            if func_start_ea != idc.BADADDR:
                xrefs = idautils.XrefsTo(func_start_ea)
                xrefs_list = []
                for xref in xrefs:
                    if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                        caller_func = idc.get_func_name(xref.frm)
                        caller_ea = xref.frm 
                        caller_xrefs = idautils.XrefsFrom(caller_ea) 
                        # for caller_xref in caller_xrefs:
                        #     caller_func_xref = idc.get_func_name(caller_xref.frm)
                        #     caller_func_ea = caller_xref.frm
                        #     print("caller_func_xref: ", caller_func_xref, hex(caller_func_ea))
                        xrefs_list.append((caller_func, hex(xref.frm)))
                return xrefs_list
        return []


    def search_vuln_func(self):
        results = []
        
        udf_result=[]

        exec_func_list = [
            'system', 'exec', 'popen', 'ShellExecute', 'ShellExecuteA', 'ShellExecuteW',
            'CreateProcess', 'CreateProcessA', 'CreateProcessW'
        ]
        exec_func_list += ['.' + func_name for func_name in exec_func_list]

        file_func_list = [
            'open', 'fopen', 'access', 'stat', 'chdir', 'mkdir', 'rmdir', 'unlink', 'remove', 'rename',
            'open64', 'fopen64', 'access64', 'stat64', 'chdir', 'mkdir64', 'rmdir64', 'unlink64', 'remove64', 'rename64'
        ]
        file_func_list += ['.' + func_name for func_name in file_func_list]

        read_calls = []
        read_calls_name = []
        read_calls_caller = []
        new_results = []
        for func_ea in idautils.Functions():
            func_name = idc.get_func_name(func_ea)
            if self.check(func_name) is True or func_name in exec_func_list or func_name in file_func_list:
                xrefs_list = self.find_function_xrefs(func_name)
                for xref in xrefs_list:
                    caller_func, caller_addr= xref
                    args = self.get_func_arguments(caller_addr)
                    results.append({
                        'where': hex(func_ea),
                        'caller_function': caller_func,
                        'vulnerable_function': idc.get_func_name(func_ea),
                        'call_address': caller_addr,
                        'arguments': args, 
                        'type': 'Xrefs (Priority: Low)'
                    })

                if idc.get_func_name(func_ea) in exec_func_list:
                            target_function = caller_func
                            target_addr = caller_addr
                            arg = args
                            if arg in [d['arguments'] for d in results]:
                                new_results.append({
                                    'where': hex(func_ea),
                                    'caller_function': caller_func,
                                    'vulnerable_function': idc.get_func_name(func_ea),
                                    'call_address': caller_addr,
                                    'arguments': args,
                                    'type': f'{target_function} -> {idc.get_func_name(func_ea)} command injection'
                                })
                                while(self.find_function_xrefs(target_function)):
                                    deep_xrefs = self.find_function_xrefs(target_function)
                                    if deep_xrefs:
                                        for xref in deep_xrefs:
                                            deep_caller_func, deep_caller_addr = xref
                                            head = self.get_function_start_address(idc.get_name_ea_simple(deep_caller_func))
                                            current_func_end = idc.get_func_attr(head, idc.FUNCATTR_END)
                                            while head != idc.BADADDR and head < current_func_end:
                                                if idc.print_insn_mnem(head) == "BL":
                                                    next_call_address = idc.get_operand_value(head, 0)
                                                    next_call_func_name = idc.get_func_name(next_call_address)
                                                    if next_call_func_name and next_call_func_name in sock_func_list:
                                                        new_result = ({
                                                            'where': target_addr,
                                                            'caller_function': deep_caller_func,
                                                            'vulnerable_function': target_function,
                                                            'call_address': deep_caller_addr,
                                                            'arguments': self.get_func_arguments(deep_caller_addr),
                                                            'type': f'Also {xref[0]} called {target_function} -> {idc.get_func_name(func_ea)} command injection'
                                                        })
                                                        if new_result not in new_results:
                                                            new_results.append(new_result)
                                                            if not self.find_function_xrefs(xref[0]):
                                                                start_address = self.get_function_start_address_by_name(xref[0])
                                                                final_result = ({
                                                                    'where': hex(start_address),
                                                                    'caller_function': deep_caller_func,
                                                                    'vulnerable_function': f'{xref[0]}',
                                                                    'call_address': hex(start_address),
                                                                    'arguments': self.get_func_arguments(self.get_function_start_address_by_name(deep_caller_func)),
                                                                    'type': f'Start with {xref[0]}, {xref[0]} called {target_function} -> {idc.get_func_name(func_ea)} command injection'
                                                                })
                                                                if not final_result in new_results:
                                                                    new_results.append(final_result)
                                                head = idc.next_head(head)
                                    target_function = deep_caller_func
                                    target_addr = deep_caller_addr
                                    
                            results.extend(new_results)
                            new_results = []



        for call_address in read_calls:
            head = call_address
            while head != idc.BADADDR:
                if idc.print_insn_mnem(head) == "BL":
                    next_call_address = idc.get_operand_value(head, 0)
                    next_call_func_name = idc.get_func_name(next_call_address)
                    if next_call_func_name in exec_func_list:
                        args = []
                        current_stack = idc.get_spd(call_address)
                        num_args = 4
                        for i in range(num_args):
                            if idc.__EA64__:
                                arg_value = idc.get_wide_qword(current_stack)
                                current_stack += 8 
                            else:
                                arg_value = idc.get_wide_dword(current_stack)
                                current_stack += 4 
                            args.append(arg_value)

                        results.append({
                            'where': read_calls_caller[read_calls.index(call_address)],
                            'caller_function': idc.get_func_name(call_address),
                            'vulnerable_function': next_call_func_name,
                            'call_address': hex(next_call_address),
                            'arguments': args,
                            'type': f'Maybe {read_calls_name[0]} command injection'
                        })
                    elif next_call_func_name in file_func_list:
                        args = []
                        current_stack = idc.get_spd(call_address)
                        num_args = 4
                        for i in range(num_args):
                            arg_value = idc.get_wide_dword(current_stack) if idc.__EA64__ else idc.get_wide_qword(current_stack)
                            args.append(arg_value)
                            current_stack += 4 if idc.__EA64__ else 4

                        results.append({
                            'where': read_calls_caller[read_calls.index(call_address)],
                            'caller_function': idc.get_func_name(call_address),
                            'vulnerable_function': next_call_func_name,
                            'call_address': hex(next_call_address),
                            'arguments': args,
                            'type': f'Maybe {read_calls_name[0]} path traversal (Type 1)'
                        })
                    elif next_call_func_name in self.get_user_defined_functions():
                        args = []
                        current_stack = idc.get_spd(call_address)
                        num_args = 4
                        for i in range(num_args):
                            arg_value = idc.get_wide_dword(current_stack) if idc.__EA64__ else idc.get_wide_qword(current_stack)
                            args.append(arg_value)
                            current_stack += 4 if idc.__EA64__ else 4

                        results.append({
                            'where': read_calls_caller[read_calls.index(call_address)],
                            'caller_function': idc.get_func_name(call_address),
                            'vulnerable_function': next_call_func_name,
                            'call_address': hex(next_call_address),
                            'arguments': args,
                            'type': f'Tracing {read_calls_name[0]} UDF call to {next_call_func_name} (use for {read_calls_name[0]} path traversal (Parameter sender) advanced search)'
                        })

                head = idc.next_head(head)

        return results



    def advanced_search_vuln_func(self):
        file_func_list = [
             'open', 'fopen', 'access', 'stat', 'chdir', 'mkdir', 'rmdir', 'unlink', 'remove', 'rename',
            'open64', 'fopen64', 'access64', 'stat64', 'chdir', 'mkdir64', 'rmdir64', 'unlink64', 'remove64', 'rename64'
        ]
        
        file_func_list += ['.' + func_name for func_name in file_func_list]
        results = []
        ud_functions = self.get_user_defined_functions()
        for call_info in self.search_vuln_func():
            if call_info['type'] == 'Maybe exec command injection':
                pass
            elif call_info['type'] == 'Maybe open path traversal (Type 1)':
                where = call_info['where']
                func_name = call_info['vulnerable_function']
                # func_name = func_name.split('(')[0]
                func_ea = idc.get_name_ea_simple(func_name)
                if func_name in ud_functions:
                    for (startea, endea) in idautils.Chunks(func_ea):
                        for head in idautils.Heads(startea, endea):
                            if idc.print_insn_mnem(head) == "bl":
                                call_address = idc.get_operand_value(head, 0)
                                call_func_name = idc.get_func_name(call_address)
                                current_stack = idc.get_spd(call_address)
                                args = []
                                num_args = 4
                                for i in range(num_args):
                                    arg_value = idc.get_wide_dword(current_stack) if idc.__EA64__ else idc.get_wide_qword(current_stack)
                                    current_stack += 4 if idc.__EA64__ else 4
                                    args.append(arg_value)
                                if call_func_name in ud_functions:
                                    for (startea, endea) in idautils.Chunks(call_address):
                                        for head in idautils.Heads(startea, endea):
                                            if idc.print_insn_mnem(head) == "bl":
                                                target_call_address = idc.get_operand_value(head, 0)
                                                target_func_name = idc.get_func_name(target_call_address)
                                                if target_func_name in file_func_list:
                                                    results.append({
                                                        'where': where,
                                                        'caller_function': call_func_name,
                                                        'vulnerable_function': f'{target_func_name}, {target_func_name}',
                                                        'call_address': call_address,
                                                        'arguments': args,
                                                        'type': f'Maybe {call_func_name} open path traversal (Parameter sender, File vulnerable)'
                                                    })

        return results
    

    def display_results(self, results):
        self.result_table.setRowCount(len(results))
        self.result_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        for idx, result in enumerate(results):
            self.result_table.setItem(idx, 0, QtWidgets.QTableWidgetItem(result['where']))
            self.result_table.setItem(idx, 1, QtWidgets.QTableWidgetItem(result['caller_function']))
            self.result_table.setItem(idx, 2, QtWidgets.QTableWidgetItem(result['vulnerable_function']))
            self.result_table.setItem(idx, 3, QtWidgets.QTableWidgetItem(result['call_address']))
            args_item = QtWidgets.QTableWidgetItem(", ".join(str(arg) for arg in result['arguments']))
            args_item.setToolTip(", ".join(str(arg) for arg in result['arguments']))
            self.result_table.setItem(idx, 4, args_item)
            self.result_table.setItem(idx, 5, QtWidgets.QTableWidgetItem(result['type']))

        self.result_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)

    def search_and_display_results(self):
        results = self.search_vuln_func()
        self.display_results(results)
                    
    def OnClose(self, form):
        pass


plg = Form()
plg.Show("Banalyzer")