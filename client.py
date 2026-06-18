# client.py
import tkinter as tk
from tkinter import ttk
import requests
import threading
import time
from plyer import notification

SERVER = "http://100.111.94.77:5000"

BG = "#111111"
BG_PANEL = "#1a1a1a"
FG = "#eeeeee"
ORANGE = "#ff9900"
ORANGE_LIGHT = "#ffb84d"
BORDER = "#333333"

seen_ids = set()


def poll_notifications():
    while True:
        try:
            r = requests.get(f"{SERVER}/check-new", timeout=3)
            data = r.json()
            if data.get("new"):
                for t in data["tickets"]:
                    if t["id"] not in seen_ids:
                        seen_ids.add(t["id"])
                        notification.notify(
                            title="🚨 Novo Alerta de Segurança",
                            message=f"{t['rule']}\nIP: {t['ip']} | Nível: {t['level']}",
                            timeout=8,
                        )
        except Exception as e:
            print("Erro no polling:", e)
        time.sleep(3)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOC Dashboard")
        self.geometry("950x650")
        self.configure(bg=BG)

        self.setup_style()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.stats_frame = tk.Frame(self.notebook, bg=BG)
        self.tickets_frame = tk.Frame(self.notebook, bg=BG)
        self.detail_frame = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.stats_frame, text="  Estatísticas  ")
        self.notebook.add(self.tickets_frame, text="  Tickets  ")
        # Detail tab is added only when a ticket is selected
        self.detail_tab_visible = False

        self.build_stats_tab()
        self.build_tickets_tab()
        self.build_detail_tab()

        self.all_tickets = []
        self.selected_ticket_id = None

        self.refresh_loop()

    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL,
            foreground=FG,
            padding=(16, 8),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ORANGE)],
            foreground=[("selected", "#111111")],
        )

        style.configure(
            "Treeview",
            background=BG_PANEL,
            foreground=FG,
            fieldbackground=BG_PANEL,
            rowheight=26,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#222222",
            foreground=ORANGE_LIGHT,
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#3a2a10")],
            foreground=[("selected", ORANGE_LIGHT)],
        )

        style.configure(
            "TRadiobutton", background=BG, foreground=FG, font=("Segoe UI", 9)
        )
        style.configure(
            "TCombobox", fieldbackground=BG_PANEL, background=BG_PANEL, foreground=FG
        )

        style.configure(
            "Orange.TButton",
            background=ORANGE,
            foreground="#111111",
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map("Orange.TButton", background=[("active", ORANGE_LIGHT)])

    # ---------------- STATS TAB ----------------
    def build_stats_tab(self):
        container = tk.Frame(self.stats_frame, bg=BG)
        container.pack(expand=True, pady=20)

        tk.Label(
            container,
            text="Visão Geral",
            font=("Segoe UI", 18, "bold"),
            bg=BG,
            fg=ORANGE,
        ).pack(pady=(0, 15))

        self.cards_frame = tk.Frame(container, bg=BG)
        self.cards_frame.pack(pady=10)

        self.card_labels = {}
        for key in ["Total", "Novos", "Em Análise", "Fechados"]:
            card = tk.Frame(
                self.cards_frame,
                bg=BG_PANEL,
                highlightbackground=BORDER,
                highlightthickness=1,
                width=160,
                height=90,
            )
            card.pack(side="left", padx=10)
            card.pack_propagate(False)

            num = tk.Label(
                card, text="0", font=("Segoe UI", 22, "bold"), bg=BG_PANEL, fg=ORANGE
            )
            num.pack(pady=(15, 0))
            tk.Label(
                card, text=key, font=("Segoe UI", 10), bg=BG_PANEL, fg="#aaaaaa"
            ).pack()
            self.card_labels[key] = num

        tk.Label(
            container,
            text="Últimos 3 tickets abertos",
            font=("Segoe UI", 13, "bold"),
            bg=BG,
            fg=ORANGE_LIGHT,
        ).pack(pady=(30, 10))

        self.last3_frame = tk.Frame(container, bg=BG)
        self.last3_frame.pack()

    # ---------------- TICKETS TAB ----------------
    def build_tickets_tab(self):
        top_bar = tk.Frame(self.tickets_frame, bg=BG)
        top_bar.pack(pady=(15, 10))

        self.filter_var = tk.StringVar(value="Todos")
        for status in ["Todos", "Novo", "Em Análise", "Fechado"]:
            ttk.Radiobutton(
                top_bar,
                text=status,
                variable=self.filter_var,
                value=status,
                command=self.refresh_tickets_list,
            ).pack(side="left", padx=8)

        table_container = tk.Frame(self.tickets_frame, bg=BG)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("id", "timestamp", "agent", "ip", "rule", "level", "status")
        headers = {
            "id": "ID",
            "timestamp": "Hora",
            "agent": "Agente",
            "ip": "IP",
            "rule": "Regra",
            "level": "Nível",
            "status": "Estado",
        }

        self.tree = ttk.Treeview(table_container, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=headers[col])
            width = 70 if col in ("id", "level") else 140
            self.tree.column(
                col, width=width, anchor="center" if col in ("level",) else "w"
            )
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_ticket_select)

        tk.Label(
            self.tickets_frame,
            text="Duplo clique num ticket para ver detalhes",
            font=("Segoe UI", 9, "italic"),
            bg=BG,
            fg="#888888",
        ).pack(pady=(0, 10))

    # ---------------- DETAIL TAB ----------------
    def build_detail_tab(self):
        container = tk.Frame(self.detail_frame, bg=BG)
        container.pack(expand=True, pady=30)

        self.detail_id_label = tk.Label(
            container, text="Ticket", font=("Segoe UI", 16, "bold"), bg=BG, fg=ORANGE
        )
        self.detail_id_label.pack(pady=(0, 20))

        card = tk.Frame(
            container, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1
        )
        card.pack(padx=10, pady=10)

        info_frame = tk.Frame(card, bg=BG_PANEL)
        info_frame.pack(padx=30, pady=20)

        self.detail_fields = {}
        labels = ["Data/Hora", "Agente", "IP", "Regra", "Nível"]
        for i, label in enumerate(labels):
            tk.Label(
                info_frame,
                text=f"{label}:",
                font=("Segoe UI", 11, "bold"),
                bg=BG_PANEL,
                fg="#aaaaaa",
            ).grid(row=i, column=0, sticky="e", padx=10, pady=6)
            value_label = tk.Label(
                info_frame, text="-", font=("Segoe UI", 11), bg=BG_PANEL, fg=FG
            )
            value_label.grid(row=i, column=1, sticky="w", padx=10, pady=6)
            self.detail_fields[label] = value_label

        status_frame = tk.Frame(container, bg=BG)
        status_frame.pack(pady=25)

        tk.Label(
            status_frame,
            text="Estado:",
            font=("Segoe UI", 11, "bold"),
            bg=BG,
            fg=ORANGE_LIGHT,
        ).pack(side="left", padx=8)
        self.status_var = tk.StringVar()
        status_menu = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=["Novo", "Em Análise", "Fechado"],
            state="readonly",
            width=15,
        )
        status_menu.pack(side="left", padx=8)

        ttk.Button(
            status_frame,
            text="Atualizar Estado",
            style="Orange.TButton",
            command=self.update_status,
        ).pack(side="left", padx=15)

        back_btn = ttk.Button(
            container, text="← Voltar aos Tickets", command=self.close_detail_tab
        )
        back_btn.pack(pady=10)

    def on_ticket_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])["values"]
        self.selected_ticket_id = values[0]

        self.detail_id_label.config(text=f"Ticket #{values[0]}")
        self.detail_fields["Data/Hora"].config(text=values[1])
        self.detail_fields["Agente"].config(text=values[2])
        self.detail_fields["IP"].config(text=values[3])
        self.detail_fields["Regra"].config(text=values[4])
        self.detail_fields["Nível"].config(text=values[5])
        self.status_var.set(values[6])

        if not self.detail_tab_visible:
            self.notebook.add(self.detail_frame, text="  Detalhe  ")
            self.detail_tab_visible = True

        self.notebook.select(self.detail_frame)

    def close_detail_tab(self):
        if self.detail_tab_visible:
            self.notebook.forget(self.detail_frame)
            self.detail_tab_visible = False
        self.notebook.select(self.tickets_frame)

    def update_status(self):
        if not self.selected_ticket_id:
            return
        try:
            requests.post(
                f"{SERVER}/tickets/{self.selected_ticket_id}/status",
                json={"status": self.status_var.get()},
                timeout=3,
            )
            self.refresh_data()
        except Exception as e:
            print("Erro ao atualizar:", e)

    def refresh_tickets_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        filter_value = self.filter_var.get()
        for t in reversed(self.all_tickets):
            if filter_value != "Todos" and t["status"] != filter_value:
                continue
            self.tree.insert(
                "",
                "end",
                values=(
                    t["id"],
                    t["timestamp"],
                    t["agent"],
                    t["ip"],
                    t["rule"],
                    t["level"],
                    t["status"],
                ),
            )

    def refresh_data(self):
        try:
            r = requests.get(f"{SERVER}/tickets", timeout=3)
            self.all_tickets = r.json()

            total = len(self.all_tickets)
            novo = len([t for t in self.all_tickets if t["status"] == "Novo"])
            analise = len([t for t in self.all_tickets if t["status"] == "Em Análise"])
            fechado = len([t for t in self.all_tickets if t["status"] == "Fechado"])

            self.card_labels["Total"].config(text=str(total))
            self.card_labels["Novos"].config(text=str(novo))
            self.card_labels["Em Análise"].config(text=str(analise))
            self.card_labels["Fechados"].config(text=str(fechado))

            for widget in self.last3_frame.winfo_children():
                widget.destroy()

            last3 = list(reversed(self.all_tickets))[:3]
            if not last3:
                tk.Label(
                    self.last3_frame,
                    text="Sem tickets ainda.",
                    bg=BG,
                    fg="#888888",
                    font=("Segoe UI", 10, "italic"),
                ).pack()
            for t in last3:
                row = tk.Frame(
                    self.last3_frame,
                    bg=BG_PANEL,
                    highlightbackground=BORDER,
                    highlightthickness=1,
                )
                row.pack(fill="x", pady=4, ipady=6, ipadx=10)
                text = f"[{t['timestamp']}]  {t['rule']}  |  IP: {t['ip']}  |  Nível: {t['level']}  |  Estado: {t['status']}"
                tk.Label(
                    row, text=text, bg=BG_PANEL, fg=FG, font=("Segoe UI", 9), anchor="w"
                ).pack(fill="x", padx=10)

            self.refresh_tickets_list()
        except Exception as e:
            print("Erro a atualizar dados:", e)

    def refresh_loop(self):
        self.refresh_data()
        self.after(3000, self.refresh_loop)


if __name__ == "__main__":
    threading.Thread(target=poll_notifications, daemon=True).start()
    app = App()
    app.mainloop()
