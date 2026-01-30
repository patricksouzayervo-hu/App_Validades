from kivy.uix.screenmanager import ScreenManager
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatIconButton, MDFillRoundFlatButton, MDRectangleFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon
from kivy.utils import get_color_from_hex
from kivy.app import App
import sqlite3
from datetime import datetime
import csv
import os

def caminho_arquivo(nome):
    app = App.get_running_app()
    if app:
        return os.path.join(app.user_data_dir, nome)
    return nome

# =========================
# BANCO DE DADOS
# =========================
def criar_banco():
    conn = sqlite3.connect(caminho_arquivo("validades.db"))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descricao TEXT,
            validade TEXT,
            departamento TEXT,
            quantidade INTEGER
        )
    """)
    conn.commit()
    conn.close()

# =========================
# FUNÇÃO PARA GERAR CSV
# =========================
def gerar_csv():
    conn = sqlite3.connect(caminho_arquivo("validades.db"))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT codigo, descricao, validade, departamento, quantidade
        FROM produtos
        ORDER BY validade
    """)
    dados = cursor.fetchall()
    conn.close()

    if not dados:
        print("Nenhum dado para gerar CSV.")
        return

    nome_arquivo = caminho_arquivo("relatorio_validades.csv")
    with open(nome_arquivo, "w", newline="", encoding="utf-8-sig") as arquivo_csv:
        writer = csv.writer(arquivo_csv, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(["Código", "Descrição", "Validade", "Departamento", "Quantidade", "Dias Restantes"])

        hoje = datetime.today()
        for codigo, descricao, validade_str, departamento, quantidade in dados:
            try:
                validade = datetime.strptime(validade_str, "%d/%m/%Y")
                dias_restantes = (validade - hoje).days
                if dias_restantes < 0:
                    dias_texto = f"Vencido ({abs(dias_restantes)} dias)"
                else:
                    dias_texto = f"{dias_restantes} dias"
            except:
                dias_texto = "Inválido"

            codigo_texto = f"'{codigo}"
            writer.writerow([codigo_texto, descricao, validade_str, departamento, quantidade, dias_texto])

    print(f"CSV gerado com sucesso: {nome_arquivo}")

# =========================
# MENU PRINCIPAL
# =========================
class MenuScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = MDBoxLayout(orientation="vertical")

        header = MDBoxLayout(
            size_hint_y=None,
            height=dp(80),
            md_bg_color=get_color_from_hex("#007bff"),
            padding=[16, 0, 16, 0]
        )
        titulo = MDLabel(
            text="Controle de Validades",
            halign="center",
            valign="middle",
            font_style="H5",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        titulo.bind(size=titulo.setter("text_size"))
        header.add_widget(titulo)

        cal_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(200),
        )
        cal_icon = MDIconButton(
            icon="calendar-month",
            icon_size="72sp",
            pos_hint={"center_x": 0.5},
            theme_text_color="Custom",
            text_color=(0.1, 0.6, 0.9, 1)
        )
        cal_box.add_widget(cal_icon)

        content = MDBoxLayout(
            orientation="vertical",
            spacing=20,
            padding=[24, 24, 24, 24]
        )

        def menu_button(text, icon, color, action):
            return MDRectangleFlatIconButton(
                text=text,
                icon=icon,
                size_hint=(1, None),
                height=dp(96),
                md_bg_color=color,
                text_color=(1, 1, 1, 1),
                on_release=action
            )

        content.add_widget(menu_button(
            "Inserir Produto",
            "plus-box",
            get_color_from_hex("#28a745"),
            lambda x: self.ir_tela("inserir")
        ))

        content.add_widget(menu_button(
            "Consultar Produtos",
            "magnify",
            get_color_from_hex("#007bff"),
            lambda x: self.ir_tela("consultar")
        ))

        content.add_widget(menu_button(
            "Validades / Alertas",
            "alert-circle",
            get_color_from_hex("#ff8c00"),
            lambda x: self.ir_tela("validades")
        ))

        content.add_widget(menu_button(
            "Gerar Relatório",
            "file-document",
            get_color_from_hex("#17a2b8"),
            lambda x: gerar_csv()
        ))

        root.add_widget(header)
        root.add_widget(cal_box)
        root.add_widget(content)
        self.add_widget(root)

    def ir_tela(self, tela):
        self.manager.current = tela

# =========================
# INSERIR PRODUTO
# =========================
class InserirProdutoScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.departamentos = ["Bazar", "Bebidas", "Carnes", "Commodities", "Flc", "Flv", "Higiene", "Limpeza", "Mercearia", "Padaria"]

        root = MDBoxLayout(orientation="vertical")

        content = MDBoxLayout(
            orientation="vertical",
            spacing=16,
            padding=[24, 24, 24, 24]
        )

        self.txt_codigo = MDTextField(hint_text="Código", icon_left="identifier")
        self.txt_descricao = MDTextField(hint_text="Descrição", icon_left="text-box")
        self.txt_validade = MDTextField(hint_text="Validade (DD/MM/AAAA)", icon_left="calendar")
        self.txt_quantidade = MDTextField(hint_text="Quantidade", icon_left="counter", input_filter="int")
        self.txt_departamento = MDTextField(hint_text="Departamento", icon_left="domain", readonly=True)

        self.menu_departamentos = MDDropdownMenu(
            caller=self.txt_departamento,
            items=[{"text": d, "on_release": lambda x=d: self.set_departamento(x)} for d in self.departamentos],
            width_mult=4
        )
        self.txt_departamento.bind(on_touch_down=self.abrir_menu)

        btn_salvar = MDFillRoundFlatButton(
            text="Salvar",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#28a745"),
            on_release=self.salvar
        )
        btn_voltar = MDFillRoundFlatButton(
            text="Voltar",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#6c757d"),
            on_release=lambda x: self.voltar()
        )

        for w in [
            self.txt_codigo, self.txt_descricao, self.txt_validade,
            self.txt_quantidade, self.txt_departamento,
            btn_salvar, btn_voltar
        ]:
            content.add_widget(w)

        root.add_widget(content)
        self.add_widget(root)

    def abrir_menu(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.menu_departamentos.open()

    def set_departamento(self, dep):
        self.txt_departamento.text = dep
        self.menu_departamentos.dismiss()

    def salvar(self, instance):
        if not all([self.txt_codigo.text.strip(),
                    self.txt_descricao.text.strip(),
                    self.txt_validade.text.strip(),
                    self.txt_quantidade.text.strip(),
                    self.txt_departamento.text.strip()]):
            dialog = MDDialog(
                title="Aviso",
                text="Todos os campos são obrigatórios.\nQuantidade pode ser 0.",
                buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
            )
            dialog.open()
            return

        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO produtos (codigo, descricao, validade, departamento, quantidade)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.txt_codigo.text,
            self.txt_descricao.text,
            self.txt_validade.text,
            self.txt_departamento.text,
            int(self.txt_quantidade.text)
        ))
        conn.commit()
        conn.close()

        self.txt_codigo.text = ""
        self.txt_descricao.text = ""
        self.txt_validade.text = ""
        self.txt_quantidade.text = ""
        self.txt_departamento.text = ""
        dialog = MDDialog(
            title="Sucesso",
            text="Produto salvo com sucesso!",
            buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    def voltar(self):
        self.manager.current = "menu"

# =========================
# CONSULTAR PRODUTOS
# =========================
class ConsultarProdutosScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.produto_selecionado = None

        root = MDBoxLayout(orientation="vertical")

        content = MDBoxLayout(
            orientation="vertical",
            spacing=12,
            padding=[24, 24, 24, 24]
        )

        self.txt_busca = MDTextField(
            hint_text="Buscar Produto pelo Código",
            icon_left="magnify"
        )
        self.txt_busca.bind(text=self.buscar)

        self.lista = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.lista.bind(minimum_height=self.lista.setter('height'))
        scroll = MDScrollView()
        scroll.add_widget(self.lista)

        self.btn_editar = MDFillRoundFlatButton(
            text="Editar Produto",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#007bff"),
            on_release=self.editar_produto,
            disabled=True
        )
        self.btn_deletar = MDFillRoundFlatButton(
            text="Deletar Produto",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#dc3545"),
            on_release=self.deletar_produto,
            disabled=True
        )
        btn_voltar = MDFillRoundFlatButton(
            text="Voltar",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#6c757d"),
            on_release=lambda x: self.voltar()
        )

        content.add_widget(self.txt_busca)
        content.add_widget(scroll)
        content.add_widget(self.btn_editar)
        content.add_widget(self.btn_deletar)
        content.add_widget(btn_voltar)

        root.add_widget(content)
        self.add_widget(root)

    def on_pre_enter(self):
        self.carregar()

    def carregar(self, filtro=""):
        self.lista.clear_widgets()
        self.produto_selecionado = None
        self.btn_editar.disabled = True
        self.btn_deletar.disabled = True

        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()

        if filtro:
            cursor.execute(
                "SELECT id, codigo, descricao, validade, departamento, quantidade FROM produtos WHERE codigo LIKE ?",
                (f"%{filtro}%",)
            )
        else:
            cursor.execute(
                "SELECT id, codigo, descricao, validade, departamento, quantidade FROM produtos"
            )

        for id_, codigo, descricao, validade, departamento, quantidade in cursor.fetchall():
            card = MDCard(
                orientation="vertical",
                padding=15,
                size_hint_y=None,
                height=dp(120),
                md_bg_color=get_color_from_hex("#f0f0f0"),
                radius=[10, 10, 10, 10],
                elevation=4
            )

            card_layout = MDBoxLayout(orientation="vertical", spacing=5, size_hint_x=1)
            linha_codigo = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_x=1)
            linha_codigo.add_widget(MDLabel(text=f"Código: {codigo}", size_hint_x=1, halign="left"))
            card_layout.add_widget(linha_codigo)

            card_layout.add_widget(MDLabel(text=f"{descricao}", size_hint_x=1, halign="left"))
            card_layout.add_widget(MDLabel(text=f"Validade: {validade} | Qtd: {quantidade} | Dept: {departamento}",
                                           size_hint_x=1, halign="left"))

            card.add_widget(card_layout)
            card.produto_id = id_
            card.bind(on_release=self.selecionar_item)
            self.lista.add_widget(card)

        conn.close()

    def selecionar_item(self, instance):
        self.produto_selecionado = instance.produto_id
        self.btn_editar.disabled = False
        self.btn_deletar.disabled = False

    def editar_produto(self, instance):
        if self.produto_selecionado:
            self.manager.get_screen("editar").carregar_produto(self.produto_selecionado)
            self.manager.current = "editar"

    def deletar_produto(self, instance):
        if self.produto_selecionado:
            dialog = MDDialog(
                title="Confirmação",
                text="Deseja realmente deletar este produto?",
                buttons=[
                    MDFillRoundFlatButton(text="Cancelar", on_release=lambda x: dialog.dismiss()),
                    MDFillRoundFlatButton(text="Deletar", on_release=self.confirmar_deletar)
                ]
            )
            dialog.open()

    def confirmar_deletar(self, instance):
        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produtos WHERE id=?", (self.produto_selecionado,))
        conn.commit()
        conn.close()
        self.carregar()
        dialog = MDDialog(
            title="Sucesso",
            text="Produto deletado com sucesso!",
            buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    def buscar(self, instance, value):
        self.carregar(value.strip())

    def voltar(self):
        self.manager.current = "menu"

# =========================
# EDITAR PRODUTO
# =========================
class EditarProdutoScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.produto_id = None
        self.departamentos = ["Bazar", "Bebidas", "Carnes", "Commodities", "Flc", "Flv", "Higiene", "Limpeza", "Mercearia", "Padaria"]

        root = MDBoxLayout(orientation="vertical")
        content = MDBoxLayout(
            orientation="vertical",
            spacing=16,
            padding=[24, 24, 24, 24]
        )

        self.txt_codigo = MDTextField(hint_text="Código", icon_left="identifier")
        self.txt_descricao = MDTextField(hint_text="Descrição", icon_left="text-box")
        self.txt_validade = MDTextField(hint_text="Validade (DD/MM/AAAA)", icon_left="calendar")
        self.txt_quantidade = MDTextField(hint_text="Quantidade", icon_left="counter", input_filter="int")
        self.txt_departamento = MDTextField(hint_text="Departamento", icon_left="domain", readonly=True)

        self.menu_departamentos = MDDropdownMenu(
            caller=self.txt_departamento,
            items=[{"text": d, "on_release": lambda x=d: self.set_departamento(x)} for d in self.departamentos],
            width_mult=4
        )
        self.txt_departamento.bind(on_touch_down=self.abrir_menu)

        btn_salvar = MDFillRoundFlatButton(
            text="Salvar",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#28a745"),
            on_release=self.salvar
        )
        btn_voltar = MDFillRoundFlatButton(
            text="Voltar",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#6c757d"),
            on_release=lambda x: self.voltar()
        )

        for w in [self.txt_codigo, self.txt_descricao, self.txt_validade,
                  self.txt_quantidade, self.txt_departamento,
                  btn_salvar, btn_voltar]:
            content.add_widget(w)

        root.add_widget(content)
        self.add_widget(root)

    def abrir_menu(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.menu_departamentos.open()

    def set_departamento(self, dep):
        self.txt_departamento.text = dep
        self.menu_departamentos.dismiss()

    def carregar_produto(self, produto_id):
        self.produto_id = produto_id
        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, descricao, validade, departamento, quantidade FROM produtos WHERE id=?",
                       (produto_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.txt_codigo.text = row[0]
            self.txt_descricao.text = row[1]
            self.txt_validade.text = row[2]
            self.txt_departamento.text = row[3]
            self.txt_quantidade.text = str(row[4])

    def salvar(self, instance):
        if not all([self.txt_codigo.text.strip(),
                    self.txt_descricao.text.strip(),
                    self.txt_validade.text.strip(),
                    self.txt_quantidade.text.strip(),
                    self.txt_departamento.text.strip()]):
            dialog = MDDialog(
                title="Aviso",
                text="Todos os campos são obrigatórios.\nQuantidade pode ser 0.",
                buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
            )
            dialog.open()
            return

        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE produtos SET codigo=?, descricao=?, validade=?, departamento=?, quantidade=? WHERE id=?
        """, (
            self.txt_codigo.text,
            self.txt_descricao.text,
            self.txt_validade.text,
            self.txt_departamento.text,
            int(self.txt_quantidade.text),
            self.produto_id
        ))
        conn.commit()
        conn.close()

        dialog = MDDialog(
            title="Sucesso",
            text="Produto atualizado com sucesso!",
            buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    def voltar(self):
        self.manager.current = "consultar"

# =========================
# VALIDADES / ALERTAS
# =========================
class ValidadesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=20)

        self.txt_filtro_dias = MDTextField(
            hint_text="Filtrar por dias restantes",
            icon_left="calendar-clock",
            size_hint_y=None,
            height=dp(48)
        )
        self.txt_filtro_dias.bind(text=self.filtrar_por_dias)
        layout.add_widget(self.txt_filtro_dias)

        self.scroll = MDScrollView()
        self.lista = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.lista.bind(minimum_height=self.lista.setter('height'))
        self.scroll.add_widget(self.lista)
        layout.add_widget(self.scroll)

        btn_voltar = MDFillRoundFlatButton(
            text="Voltar",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=get_color_from_hex("#6c757d"),
            on_release=lambda x: self.voltar()
        )
        layout.add_widget(btn_voltar)
        self.add_widget(layout)

    def on_pre_enter(self):
        self.atualizar_validades()
        self.mostrar_alerta_automatico()

    def atualizar_validades(self, dias_filtro=None):
        self.lista.clear_widgets()
        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigo, descricao, validade, departamento, quantidade
            FROM produtos
            ORDER BY validade
        """)
        hoje = datetime.today()

        for codigo, descricao, validade_str, departamento, quantidade in cursor.fetchall():
            try:
                validade = datetime.strptime(validade_str, "%d/%m/%Y")
                dias_restantes = (validade - hoje).days
            except:
                dias_restantes = None

            if dias_filtro is not None:
                if dias_restantes is None or dias_restantes != dias_filtro:
                    continue

            if dias_restantes is None:
                cor_fundo = get_color_from_hex("#AAAAAA")
                icon = "alert-circle"
                dias_texto = "Data inválida"
            elif dias_restantes < 0:
                cor_fundo = get_color_from_hex("#FF0000")
                icon = "close-circle"
                dias_texto = f"Vencido ({abs(dias_restantes)} dias)"
            elif dias_restantes <= 7:
                cor_fundo = get_color_from_hex("#FF5555")
                icon = "alert-circle"
                dias_texto = f"{dias_restantes} dias"
            elif dias_restantes <= 15:
                cor_fundo = get_color_from_hex("#FFCC00")
                icon = "alert"
                dias_texto = f"{dias_restantes} dias"
            else:
                cor_fundo = get_color_from_hex("#00CC00")
                icon = "check-circle"
                dias_texto = f"{dias_restantes} dias"

            card = MDCard(
                orientation="vertical",
                padding=15,
                size_hint_y=None,
                height=dp(120),
                md_bg_color=cor_fundo,
                radius=[10, 10, 10, 10],
                elevation=4
            )

            card_layout = MDBoxLayout(orientation="vertical", spacing=5, size_hint_x=1)
            linha_codigo = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_x=1)
            linha_codigo.add_widget(MDIcon(icon=icon, theme_text_color="Custom", text_color=(0,0,0,1)))
            linha_codigo.add_widget(MDLabel(
                text=f"Código: {codigo}",
                theme_text_color="Custom",
                text_color=(0,0,0,1),
                size_hint_x=1,
                halign="left"
            ))
            card_layout.add_widget(linha_codigo)
            card_layout.add_widget(MDLabel(
                text=f"{descricao}",
                theme_text_color="Custom",
                text_color=(0,0,0,1),
                size_hint_x=1,
                halign="left"
            ))
            card_layout.add_widget(MDLabel(
                text=f"Qtd: {quantidade} | Departamento: {departamento} | Restante: {dias_texto}",
                theme_text_color="Custom",
                text_color=(0,0,0,1),
                size_hint_x=1,
                halign="left"
            ))
            card.add_widget(card_layout)
            self.lista.add_widget(card)

        conn.close()

    def filtrar_por_dias(self, instance, valor):
        valor = valor.strip()
        if valor.isdigit():
            self.atualizar_validades(dias_filtro=int(valor))
        else:
            self.atualizar_validades()

    def mostrar_alerta_automatico(self):
        conn = sqlite3.connect(caminho_arquivo("validades.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT descricao, validade FROM produtos")
        hoje = datetime.today()
        produtos_alerta = []

        for descricao, validade_str in cursor.fetchall():
            try:
                validade = datetime.strptime(validade_str, "%d/%m/%Y")
                dias_restantes = (validade - hoje).days
                if dias_restantes < 0:
                    produtos_alerta.append(f"{descricao} (Vencido)")
                elif dias_restantes <= 7:
                    produtos_alerta.append(f"{descricao} ({dias_restantes} dias restantes)")
            except:
                continue
        conn.close()

        if produtos_alerta:
            texto = "Produtos críticos:\n" + "\n".join(produtos_alerta)
            dialog = MDDialog(
                title="Alertas de Validade",
                text=texto,
                size_hint=(0.8, None),
                buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
            )
            dialog.open()

    def voltar(self):
        self.manager.current = "menu"

# =========================
# APP PRINCIPAL
# =========================
class ValidadesApp(MDApp):
    def build(self):
        criar_banco()
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(InserirProdutoScreen(name="inserir"))
        sm.add_widget(ConsultarProdutosScreen(name="consultar"))
        sm.add_widget(EditarProdutoScreen(name="editar"))
        sm.add_widget(ValidadesScreen(name="validades"))
        return sm

if __name__ == "__main__":
    ValidadesApp().run()

