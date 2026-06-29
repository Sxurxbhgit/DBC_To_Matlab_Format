# import re
# import sys
# import os

# def parse_dbc(file_path):
#     """
#     Parses a DBC file and extracts Message and Signal information.
#     Returns a dictionary of messages keyed by their name.
#     """
#     messages = {}
#     current_msg = None

#     # Regex patterns
#     # Matches: BO_ 1314 IVT_Msg_Result_U1: 6 IVT_Mod
#     msg_pattern = re.compile(r"^BO_\s+(\d+)\s+(\w+):\s+(\d+)\s+(\w+)")
    
#     # Matches: SG_ SignalName [MUX] : StartBit|BitLength@ByteOrderDataType (Scale,Offset) [Min|Max] "Unit" Receivers
#     sig_pattern = re.compile(r"^\s*SG_\s+(\w+).*?:\s+(\d+)\|(\d+)@([01])([+-])\s+\(([^,]+),([^)]+)\)\s+\[.*?\]\s+\"(.*?)\"")

#     try:
#         with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
#             for line in f:
#                 # Check for Message (BO_)
#                 msg_match = msg_pattern.match(line)
#                 if msg_match:
#                     raw_id = int(msg_match.group(1))
#                     name = msg_match.group(2)
#                     dlc = int(msg_match.group(3))
#                     node = msg_match.group(4)
                    
#                     # CAN IDs in DBC use the 32nd bit to indicate EXTENDED ID
#                     real_id = raw_id & 0x1FFFFFFF
#                     is_extended = (raw_id > 0x1FFFFFFF) or (real_id > 0x7FF)
                    
#                     current_msg = {
#                         'name': name,
#                         'id_dec': real_id,
#                         'id_hex': hex(real_id)[2:].upper(),
#                         'idext': 'EXTENDED' if is_extended else 'STANDARD',
#                         'payload_size': dlc,
#                         'node': node,
#                         'signals': []
#                     }
#                     messages[name] = current_msg
#                     continue
                
#                 # Check for Signal (SG_)
#                 if current_msg is not None:
#                     sig_match = sig_pattern.match(line)
#                     if sig_match:
#                         sig = {
#                             'name': sig_match.group(1),
#                             'start_bit': int(sig_match.group(2)),
#                             'bit_length': int(sig_match.group(3)),
#                             'byte_order': 'BIG_ENDIAN' if sig_match.group(4) == '0' else 'LITTLE_ENDIAN',
#                             'data_type': 'UNSIGNED' if sig_match.group(5) == '+' else 'SIGNED',
#                             'scale': sig_match.group(6),
#                             'offset': sig_match.group(7),
#                             'units': sig_match.group(8)
#                         }
#                         current_msg['signals'].append(sig)

#     except FileNotFoundError:
#         print(f"Error: The file {file_path} was not found.")
#         sys.exit(1)

#     return messages

# def generate_matlab_script(messages, target_msgs=None, output_filename="Ev_Demo_M.m", struct_name="ECOCAN"):
#     """
#     Generates the MATLAB function string from the parsed DBC dictionary.
#     If target_msgs is provided (list of strings), only those messages are extracted.
#     """
    
#     # Filter messages based on user intent
#     if target_msgs:
#         msgs_to_process = [messages[m] for m in target_msgs if m in messages]
#         missing = [m for m in target_msgs if m not in messages]
#         if missing:
#             print(f"Warning: The following requested messages were not found in the DBC: {missing}")
#     else:
#         # If no target specified, convert EVERYTHING
#         msgs_to_process = list(messages.values())

#     if not msgs_to_process:
#         print("Error: No messages to convert. Aborting.")
#         return

#     # Start writing MATLAB file
#     lines = []
#     lines.append("function msg = Ev_Demo_M(msgname,type)")
#     lines.append("  if(255==type)")
#     lines.append("  msg = struct;")
#     lines.append(f"  msg.num={len(msgs_to_process)};")
#     lines.append("  msg.list= cell(1, msg.num);")
    
#     # Generate list block
#     for idx, msg in enumerate(msgs_to_process, start=1):
#         lines.append(f"  msg.list{{{idx}}}='{msg['name']}';")
        
#     lines.append("  else ")
#     lines.append("  msg = struct;")
#     lines.append("  switch msgname ")
    
#     # Generate cases block
#     for msg_idx, msg in enumerate(msgs_to_process, start=1):
#         lines.append("%%")
#         lines.append(f"%Network Node:{msg['node']}")
#         lines.append(f"%Message Name:{msg['name']}")
#         lines.append(f"%Message Number:{msg_idx}")
#         lines.append(f"case '{msg['name']}'")
        
#         m_name = msg['name']
#         lines.append(f"    {struct_name}.{m_name} = struct;")
#         lines.append(f"    {struct_name}.{m_name} .name = '{m_name}';")
#         lines.append(f"    {struct_name}.{m_name}.description = '{m_name}';")
#         lines.append(f"    {struct_name}.{m_name}.protocol  = 'ECOCAN';")
#         lines.append(f"    {struct_name}.{m_name}.id = hex2dec('{msg['id_hex']}');")
#         lines.append(f"    {struct_name}.{m_name}.idext = '{msg['idext']}';")
#         lines.append(f"    {struct_name}.{m_name}.payload_size ={msg['payload_size']};")
#         lines.append(f"    {struct_name}.{m_name}.interval =-1;") # Defaulting to -1 as per template
#         lines.append("")

#         # Generate signal fields
#         for s_idx, sig in enumerate(msg['signals'], start=1):
#             s_name = sig['name']
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.name = '{s_name}';")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.units = '{sig['units']}';")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.start_bit = {sig['start_bit']};")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.bit_length = {sig['bit_length']};")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.byte_order = '{sig['byte_order']}';")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.data_type = '{sig['data_type']}';")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.scale = {sig['scale']};")
#             lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.offset = {sig['offset']};")
#             lines.append("")
            
#     lines.append("  end")
#     lines.append("  try")
#     lines.append(f"    msg = {struct_name}.(msgname);")
#     lines.append("  catch")
#     lines.append("  end")
#     lines.append("end")
#     lines.append("end\n")

#     # Write output file
#     try:
#         with open(output_filename, 'w', encoding='utf-8') as f:
#             f.write('\n'.join(lines))
#         print(f"Success: MATLAB CAN dictionary generated and saved to '{output_filename}'")
#     except IOError as e:
#         print(f"Error writing to file: {e}")

# if __name__ == "__main__":
#     # -------------------------------------------------------------
#     # 1. DYNAMIC PATH RESOLUTION: Based on the new folder structure
#     # -------------------------------------------------------------
#     # Gets the directory where main.py lives (Script/)
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     # Moves up one level to the project root (PYTHON_SCRIPT_TO_ECOTRON)
#     project_root = os.path.dirname(script_dir)
    
#     # Define paths using the new directory structure
#     input_dbc_file = os.path.join(project_root, 'dbc_file', 'CANbus DBC IVT-S_01062017.dbc')
#     output_path = os.path.join(project_root, 'output_file', 'Ev_Demo_M.m')

#     # -------------------------------------------------------------
#     # 2. SETUP: Add the exact names of the messages you want to convert
#     # -------------------------------------------------------------
#     desired_messages = [
#         "IVT_Msg_Result_U1",
#         "IVT_Msg_Result_I",
#         "IVT_Msg_Result_W"
#     ]
    
#     # Parse the DBC file to a dictionary
#     parsed_dbc_data = parse_dbc(input_dbc_file)
    
#     # Generate the .m text file
#     if parsed_dbc_data:
#         generate_matlab_script(
#             messages=parsed_dbc_data, 
#             target_msgs=desired_messages, 
#             output_filename=output_path, # Now using the dynamic path
#             struct_name="ECOCAN"
#         )


import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# -------------------------------------------------------------
# 1. CORE FUNCTIONS (Parsing and Generating)
# -------------------------------------------------------------
def parse_dbc(file_path):
    messages = {}
    current_msg = None

    msg_pattern = re.compile(r"^BO_\s+(\d+)\s+(\w+):\s+(\d+)\s+(\w+)")
    sig_pattern = re.compile(r"^\s*SG_\s+(\w+).*?:\s+(\d+)\|(\d+)@([01])([+-])\s+\(([^,]+),([^)]+)\)\s+\[.*?\]\s+\"(.*?)\"")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                msg_match = msg_pattern.match(line)
                if msg_match:
                    raw_id = int(msg_match.group(1))
                    name = msg_match.group(2)
                    dlc = int(msg_match.group(3))
                    node = msg_match.group(4)
                    
                    real_id = raw_id & 0x1FFFFFFF
                    is_extended = (raw_id > 0x1FFFFFFF) or (real_id > 0x7FF)
                    
                    current_msg = {
                        'name': name,
                        'id_dec': real_id,
                        'id_hex': hex(real_id)[2:].upper(),
                        'idext': 'EXTENDED' if is_extended else 'STANDARD',
                        'payload_size': dlc,
                        'node': node,
                        'signals': []
                    }
                    messages[name] = current_msg
                    continue
                
                if current_msg is not None:
                    sig_match = sig_pattern.match(line)
                    if sig_match:
                        sig = {
                            'name': sig_match.group(1),
                            'start_bit': int(sig_match.group(2)),
                            'bit_length': int(sig_match.group(3)),
                            'byte_order': 'BIG_ENDIAN' if sig_match.group(4) == '0' else 'LITTLE_ENDIAN',
                            'data_type': 'UNSIGNED' if sig_match.group(5) == '+' else 'SIGNED',
                            'scale': sig_match.group(6),
                            'offset': sig_match.group(7),
                            'units': sig_match.group(8)
                        }
                        current_msg['signals'].append(sig)
    except Exception as e:
        raise Exception(f"Failed to read DBC file:\n{e}")

    return messages

def generate_matlab_script(messages, target_msgs, output_filename, struct_name="ECOCAN"):
    if not target_msgs:
        return False, "No messages selected to convert."

    msgs_to_process = [messages[m] for m in target_msgs if m in messages]

    if not msgs_to_process:
        return False, "None of the selected messages were found in the parsed data."

    lines = []
    lines.append("function msg = Ev_Demo_M(msgname,type)")
    lines.append("  if(255==type)")
    lines.append("  msg = struct;")
    lines.append(f"  msg.num={len(msgs_to_process)};")
    lines.append("  msg.list= cell(1, msg.num);")
    
    for idx, msg in enumerate(msgs_to_process, start=1):
        lines.append(f"  msg.list{{{idx}}}='{msg['name']}';")
        
    lines.append("  else ")
    lines.append("  msg = struct;")
    lines.append("  switch msgname ")
    
    for msg_idx, msg in enumerate(msgs_to_process, start=1):
        lines.append("%%")
        lines.append(f"%Network Node:{msg['node']}")
        lines.append(f"%Message Name:{msg['name']}")
        lines.append(f"%Message Number:{msg_idx}")
        lines.append(f"case '{msg['name']}'")
        
        m_name = msg['name']
        lines.append(f"    {struct_name}.{m_name} = struct;")
        lines.append(f"    {struct_name}.{m_name} .name = '{m_name}';")
        lines.append(f"    {struct_name}.{m_name}.description = '{m_name}';")
        lines.append(f"    {struct_name}.{m_name}.protocol  = 'ECOCAN';")
        lines.append(f"    {struct_name}.{m_name}.id = hex2dec('{msg['id_hex']}');")
        lines.append(f"    {struct_name}.{m_name}.idext = '{msg['idext']}';")
        lines.append(f"    {struct_name}.{m_name}.payload_size ={msg['payload_size']};")
        lines.append(f"    {struct_name}.{m_name}.interval =-1;") 
        lines.append("")

        for s_idx, sig in enumerate(msg['signals'], start=1):
            s_name = sig['name']
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.name = '{s_name}';")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.units = '{sig['units']}';")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.start_bit = {sig['start_bit']};")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.bit_length = {sig['bit_length']};")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.byte_order = '{sig['byte_order']}';")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.data_type = '{sig['data_type']}';")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.scale = {sig['scale']};")
            lines.append(f"    {struct_name}.{m_name}.fields{{{s_idx}}}.offset = {sig['offset']};")
            lines.append("")
            
    lines.append("  end")
    lines.append("  try")
    lines.append(f"    msg = {struct_name}.(msgname);")
    lines.append("  catch")
    lines.append("  end")
    lines.append("end")
    lines.append("end\n")

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True, f"Successfully saved to:\n{output_filename}"
    except IOError as e:
        return False, f"Error writing to file:\n{e}"


# -------------------------------------------------------------
# 2. GUI APPLICATION (Tkinter Front-End)
# -------------------------------------------------------------
class DBCConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DBC to MATLAB Converter")
        self.root.geometry("650x670")
        
        self.parsed_dbc_data = {}
        self.all_msg_names = []
        self.is_loading_ui = False
        
        # State tracking for checkboxes
        self.selected_messages = set()
        self.CHECKED = "☑"
        self.UNCHECKED = "☐"
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.script_dir)
        self.default_output_dir = os.path.join(self.project_root, 'output_file')
        
        if not os.path.exists(self.default_output_dir):
            try:
                os.makedirs(self.default_output_dir)
            except:
                self.default_output_dir = self.script_dir

        self.setup_ui()

    def setup_ui(self):
        pad_options = {'padx': 10, 'pady': 5}

        # --- Frame: DBC File Selection ---
        frame_input = ttk.LabelFrame(self.root, text="1. Select DBC File")
        frame_input.pack(fill=tk.X, **pad_options)

        self.dbc_path_var = tk.StringVar()
        ttk.Entry(frame_input, textvariable=self.dbc_path_var, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5), pady=5)
        
        self.browse_btn = ttk.Button(frame_input, text="Browse", command=self.browse_dbc)
        self.browse_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=5)

        # --- Frame: Message Selection (With Search & Checkboxes) ---
        frame_msg = ttk.LabelFrame(self.root, text="2. Search & Select Messages to Extract")
        frame_msg.pack(fill=tk.BOTH, expand=True, **pad_options)

        search_frame = ttk.Frame(frame_msg)
        search_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        self.status_lbl = ttk.Label(frame_msg, text="Awaiting file...", foreground="gray")
        self.status_lbl.pack(fill=tk.X, padx=5, pady=2)

        # Treeview (List) - Configured for checkboxes
        list_frame = ttk.Frame(frame_msg)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(list_frame, selectmode="none", columns=("Check", "Message"), show="headings", yscrollcommand=scroll.set, height=10)
        
        self.tree.heading("Check", text="✔")
        self.tree.column("Check", width=40, minwidth=40, anchor="center", stretch=tk.NO)
        
        self.tree.heading("Message", text="Available Messages (Click anywhere on row to select)", anchor=tk.W)
        self.tree.column("Message", stretch=tk.YES, width=510)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.tree.yview)

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        # Selection Buttons
        frame_sel_btns = ttk.Frame(frame_msg)
        frame_sel_btns.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(frame_sel_btns, text="Select All Visible", command=self.select_all_visible).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(frame_sel_btns, text="Clear All Selections", command=self.clear_all_selections).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # --- Frame: Output Selection ---
        frame_output = ttk.LabelFrame(self.root, text="3. Output Configuration")
        frame_output.pack(fill=tk.X, **pad_options)
        
        # Output Directory Row
        dir_frame = ttk.Frame(frame_output)
        dir_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(dir_frame, text="Folder:", width=10).pack(side=tk.LEFT)
        self.out_path_var = tk.StringVar(value=self.default_output_dir)
        ttk.Entry(dir_frame, textvariable=self.out_path_var, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        ttk.Button(dir_frame, text="Change", command=self.browse_output).pack(side=tk.RIGHT, padx=(0, 0))

        # Output Filename Row
        file_frame = ttk.Frame(frame_output)
        file_frame.pack(fill=tk.X, padx=5, pady=(2, 5))
        ttk.Label(file_frame, text="File Name:", width=10).pack(side=tk.LEFT)
        self.out_filename_var = tk.StringVar(value="Ev_Demo_M.m")
        ttk.Entry(file_frame, textvariable=self.out_filename_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        # To align the entry box with the one above, we add a dummy hidden label that matches the button width
        dummy_lbl = ttk.Label(file_frame, width=8)
        dummy_lbl.pack(side=tk.RIGHT)

        # --- Generate Button ---
        ttk.Button(self.root, text="GENERATE MATLAB SCRIPT", command=self.generate).pack(fill=tk.X, padx=10, pady=15)

    def browse_dbc(self):
        file_path = filedialog.askopenfilename(
            title="Select DBC File",
            filetypes=[("DBC files", "*.dbc"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.join(self.project_root, 'dbc_file')
        )
        if file_path:
            self.dbc_path_var.set(file_path)
            self.browse_btn.config(state=tk.DISABLED, text="Parsing...")
            self.status_lbl.config(text="Reading massive file, please wait...", foreground="blue")
            self.root.update_idletasks()
            
            self.selected_messages.clear()
            
            threading.Thread(target=self._parse_file_thread, args=(file_path,), daemon=True).start()

    def _parse_file_thread(self, file_path):
        try:
            parsed_data = parse_dbc(file_path)
            self.root.after(0, self._on_parse_complete, parsed_data, None)
        except Exception as e:
            self.root.after(0, self._on_parse_complete, None, str(e))

    def _on_parse_complete(self, parsed_data, error):
        self.browse_btn.config(state=tk.NORMAL, text="Browse")
        
        if error:
            messagebox.showerror("Error", error)
            self.status_lbl.config(text="Error parsing file.", foreground="red")
            return
            
        self.parsed_dbc_data = parsed_data
        self.all_msg_names = list(parsed_data.keys())
        
        self.status_lbl.config(text=f"Parsed {len(self.all_msg_names)} messages. Building list UI...", foreground="orange")
        self.search_var.set("")
        
        self.tree.delete(*self.tree.get_children())
        self.is_loading_ui = True
        self._populate_tree_chunked(self.all_msg_names, 0, chunk_size=200)

    def _populate_tree_chunked(self, item_list, start_idx, chunk_size=200):
        if not self.is_loading_ui:
            return 
            
        end_idx = min(start_idx + chunk_size, len(item_list))
        
        for i in range(start_idx, end_idx):
            msg_name = item_list[i]
            check_state = self.CHECKED if msg_name in self.selected_messages else self.UNCHECKED
            self.tree.insert("", tk.END, values=(check_state, msg_name))
            
        if end_idx < len(item_list):
            self.root.after(10, self._populate_tree_chunked, item_list, end_idx, chunk_size)
        else:
            self.is_loading_ui = False
            self.status_lbl.config(text=f"Ready. {len(self.selected_messages)} messages currently selected.", foreground="green")

    def on_search_change(self, *args):
        if not self.all_msg_names: return
        self.is_loading_ui = False 
        
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        
        if query == "":
            filtered_list = self.all_msg_names
        else:
            filtered_list = [m for m in self.all_msg_names if query in m.lower()]
            
        self.is_loading_ui = True
        self._populate_tree_chunked(filtered_list, 0, chunk_size=200)

    def on_tree_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
            
        values = self.tree.item(row_id, "values")
        msg_name = values[1]
        
        if msg_name in self.selected_messages:
            self.selected_messages.remove(msg_name)
            self.tree.set(row_id, "Check", self.UNCHECKED)
        else:
            self.selected_messages.add(msg_name)
            self.tree.set(row_id, "Check", self.CHECKED)
            
        self.status_lbl.config(text=f"Ready. {len(self.selected_messages)} messages currently selected.", foreground="green")

    def select_all_visible(self):
        for row_id in self.tree.get_children():
            msg_name = self.tree.item(row_id, "values")[1]
            self.selected_messages.add(msg_name)
            self.tree.set(row_id, "Check", self.CHECKED)
        self.status_lbl.config(text=f"Ready. {len(self.selected_messages)} messages currently selected.", foreground="green")

    def clear_all_selections(self):
        self.selected_messages.clear()
        for row_id in self.tree.get_children():
            self.tree.set(row_id, "Check", self.UNCHECKED)
        self.status_lbl.config(text=f"Ready. 0 messages currently selected.", foreground="green")

    def browse_output(self):
        dir_path = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.out_path_var.get()
        )
        if dir_path:
            self.out_path_var.set(dir_path)

    def generate(self):
        if not self.parsed_dbc_data:
            messagebox.showwarning("Warning", "Please load a DBC file first.")
            return
            
        target_msgs = list(self.selected_messages)
        
        if not target_msgs:
            response = messagebox.askyesno(
                "No Selection", 
                "You haven't checked any specific messages.\n\nDo you want to convert ALL parsed messages in the entire DBC file?"
            )
            if response:
                target_msgs = self.all_msg_names
            else:
                return
        
        # Format the file name correctly
        filename = self.out_filename_var.get().strip()
        if not filename:
            filename = "Ev_Demo_M.m"
        elif not filename.endswith(".m"):
            filename += ".m"
            self.out_filename_var.set(filename) # Update UI to show the appended extension
            
        output_file = os.path.join(self.out_path_var.get(), filename)
        
        success, msg = generate_matlab_script(
            messages=self.parsed_dbc_data, 
            target_msgs=target_msgs, 
            output_filename=output_file
        )
        
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = DBCConverterApp(root)
    root.lift()
    root.mainloop()