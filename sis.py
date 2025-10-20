import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, 
                             QLabel, QComboBox, QMessageBox, QFormLayout, QDialog,
                             QGroupBox, QStatusBar, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from datetime import datetime

# Conexão com o banco de dados SQLite
def init_db():
    conn = sqlite3.connect('oficina_motos.db')
    cursor = conn.cursor()
    
    # Criação das tabelas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            telefone TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS motos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            marca TEXT,
            modelo TEXT,
            placa TEXT,
            ano TEXT,
            cor TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descricao TEXT,
            quantidade INTEGER,
            preco_custo REAL,
            preco_venda REAL,
            estoque_minimo INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            moto_id INTEGER,
            descricao TEXT,
            status TEXT,
            mao_obra REAL,
            data TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (moto_id) REFERENCES motos(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS os_pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            os_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            FOREIGN KEY (os_id) REFERENCES ordens_servico(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venda_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            funcao TEXT NOT NULL,
            data_admissao TEXT,
            salario REAL,
            status TEXT DEFAULT 'Ativo'
        )
    ''')
    
    conn.commit()
    conn.close()

# Classe para gerenciar o banco de dados
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('oficina_motos.db')
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def cadastrar_cliente(self, nome, cpf, telefone):
        self.cursor.execute("INSERT INTO clientes (nome, cpf, telefone) VALUES (?, ?, ?)", 
                           (nome, cpf, telefone))
        self.conn.commit()
        return self.cursor.lastrowid

    def excluir_cliente(self, cliente_id):
        try:
            # Verificar se o cliente tem motos cadastradas
            self.cursor.execute("SELECT COUNT(*) FROM motos WHERE cliente_id = ?", (cliente_id,))
            motos_count = self.cursor.fetchone()[0]
            
            if motos_count > 0:
                return False, f"Não é possível excluir o cliente. Ele possui {motos_count} moto(s) cadastrada(s)."
            
            # Verificar se o cliente tem ordens de serviço
            self.cursor.execute("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id = ?", (cliente_id,))
            os_count = self.cursor.fetchone()[0]
            
            if os_count > 0:
                return False, f"Não é possível excluir o cliente. Ele possui {os_count} ordem(ns) de serviço."
            
            # Verificar se o cliente tem vendas
            self.cursor.execute("SELECT COUNT(*) FROM vendas WHERE cliente_id = ?", (cliente_id,))
            vendas_count = self.cursor.fetchone()[0]
            
            if vendas_count > 0:
                return False, f"Não é possível excluir o cliente. Ele possui {vendas_count} venda(s) registrada(s)."
            
            # Se passou por todas as verificações, pode excluir
            self.cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            self.conn.commit()
            return True, "Cliente excluído com sucesso!"
            
        except Exception as e:
            self.conn.rollback()
            return False, f"Erro ao excluir cliente: {str(e)}"

    def cadastrar_moto(self, cliente_id, marca, modelo, placa, ano='', cor=''):
        self.cursor.execute("INSERT INTO motos (cliente_id, marca, modelo, placa, ano, cor) VALUES (?, ?, ?, ?, ?, ?)", 
                           (cliente_id, marca, modelo, placa, ano, cor))
        self.conn.commit()
        return self.cursor.lastrowid

    def cadastrar_produto(self, codigo, descricao, quantidade, preco_custo, preco_venda, estoque_minimo):
        self.cursor.execute("INSERT INTO produtos (codigo, descricao, quantidade, preco_custo, preco_venda, estoque_minimo) VALUES (?, ?, ?, ?, ?, ?)", 
                           (codigo, descricao, quantidade, preco_custo, preco_venda, estoque_minimo))
        self.conn.commit()
        return self.cursor.lastrowid

    def listar_clientes(self):
        self.cursor.execute("SELECT id, nome FROM clientes")
        return self.cursor.fetchall()

    def listar_motos(self, cliente_id):
        self.cursor.execute("SELECT id, marca, modelo, placa FROM motos WHERE cliente_id = ?", (cliente_id,))
        return self.cursor.fetchall()

    def listar_produtos(self):
        self.cursor.execute("SELECT id, codigo, descricao, quantidade, preco_venda FROM produtos")
        return self.cursor.fetchall()

    def cadastrar_funcionario(self, nome, cpf, telefone, funcao, data_admissao, salario):
        try:
            self.cursor.execute("""INSERT INTO funcionarios (nome, cpf, telefone, funcao, data_admissao, salario) 
                                 VALUES (?, ?, ?, ?, ?, ?)""", 
                               (nome, cpf, telefone, funcao, data_admissao, salario))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # CPF já existe

    def listar_funcionarios(self):
        self.cursor.execute("SELECT id, nome, funcao, telefone, status FROM funcionarios ORDER BY nome")
        return self.cursor.fetchall()

    def excluir_funcionario(self, funcionario_id):
        try:
            # Verificar se o funcionário tem ordens de serviço associadas
            self.cursor.execute("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id IN (SELECT id FROM clientes WHERE id = ?)", (funcionario_id,))
            # Por enquanto, vamos permitir exclusão - pode ser expandido depois
            self.cursor.execute("DELETE FROM funcionarios WHERE id = ?", (funcionario_id,))
            self.conn.commit()
            return True, "Funcionário excluído com sucesso!"
        except Exception as e:
            self.conn.rollback()
            return False, f"Erro ao excluir funcionário: {str(e)}"

    def verificar_estoque(self, produto_id, quantidade):
        self.cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,))
        result = self.cursor.fetchone()
        return result[0] >= quantidade if result else False

    def atualizar_estoque(self, produto_id, quantidade):
        self.cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", 
                           (quantidade, produto_id))
        self.conn.commit()

    def criar_ordem_servico(self, cliente_id, moto_id, descricao):
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO ordens_servico (cliente_id, moto_id, descricao, status, mao_obra, data) VALUES (?, ?, ?, ?, ?, ?)", 
                           (cliente_id, moto_id, descricao, "Aberta", 0.0, data))
        self.conn.commit()
        return self.cursor.lastrowid

    def adicionar_peca_os(self, os_id, produto_id, quantidade):
        if self.verificar_estoque(produto_id, quantidade):
            self.cursor.execute("INSERT INTO os_pecas (os_id, produto_id, quantidade) VALUES (?, ?, ?)", 
                               (os_id, produto_id, quantidade))
            self.atualizar_estoque(produto_id, quantidade)
            self.conn.commit()
            return True
        return False

    def concluir_os(self, os_id, mao_obra):
        self.cursor.execute("UPDATE ordens_servico SET status = ?, mao_obra = ? WHERE id = ?", 
                           ("Concluída", mao_obra, os_id))
        self.conn.commit()

    def calcular_total_os(self, os_id):
        self.cursor.execute("SELECT SUM(p.preco_venda * op.quantidade) FROM os_pecas op JOIN produtos p ON op.produto_id = p.id WHERE op.os_id = ?", 
                           (os_id,))
        total_pecas = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT mao_obra FROM ordens_servico WHERE id = ?", (os_id,))
        mao_obra = self.cursor.fetchone()[0]
        return total_pecas + mao_obra

    def registrar_venda(self, cliente_id, produtos_quantidades):
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO vendas (cliente_id, data) VALUES (?, ?)", (cliente_id, data))
        venda_id = self.cursor.lastrowid
        total = 0
        for produto_id, quantidade in produtos_quantidades:
            if self.verificar_estoque(produto_id, quantidade):
                self.cursor.execute("INSERT INTO venda_itens (venda_id, produto_id, quantidade) VALUES (?, ?, ?)", 
                                   (venda_id, produto_id, quantidade))
                self.atualizar_estoque(produto_id, quantidade)
                self.cursor.execute("SELECT preco_venda FROM produtos WHERE id = ?", (produto_id,))
                preco_venda = self.cursor.fetchone()[0]
                total += preco_venda * quantidade
            else:
                self.conn.rollback()
                return None
        self.conn.commit()
        return total

    def listar_os(self):
        self.cursor.execute("SELECT os.id, c.nome, m.modelo, os.descricao, os.status, os.data FROM ordens_servico os JOIN clientes c ON os.cliente_id = c.id JOIN motos m ON os.moto_id = m.id")
        return self.cursor.fetchall()

    def relatorio_estoque_baixo(self):
        self.cursor.execute("SELECT codigo, descricao, quantidade FROM produtos WHERE quantidade <= estoque_minimo")
        return self.cursor.fetchall()

# Janela para cadastro de clientes
class CadastroClienteDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Cadastrar Cliente")
        self.setFixedSize(300, 200)

        layout = QFormLayout()
        self.nome = QLineEdit()
        self.cpf = QLineEdit()
        self.telefone = QLineEdit()
        
        # Validação para telefone: exatamente 11 dígitos
        telefone_validator = QRegExpValidator(QRegExp(r'\d{11}'))
        self.telefone.setValidator(telefone_validator)
        self.telefone.setPlaceholderText("11999999999")
        
        layout.addRow("Nome:", self.nome)
        layout.addRow("CPF:", self.cpf)
        layout.addRow("Telefone (11 dígitos):", self.telefone)

        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.salvar)
        layout.addWidget(btn_salvar)

        self.setLayout(layout)

    def salvar(self):
        nome = self.nome.text()
        cpf = self.cpf.text()
        telefone = self.telefone.text()
        
        if not nome:
            QMessageBox.warning(self, "Erro", "Nome é obrigatório!")
            return
            
        if len(telefone) != 11 or not telefone.isdigit():
            QMessageBox.warning(self, "Erro", "Telefone deve conter exatamente 11 dígitos!")
            return
            
        self.db.cadastrar_cliente(nome, cpf, telefone)
        QMessageBox.information(self, "Sucesso", "Cliente cadastrado com sucesso!")
        self.accept()

# Janela para cadastro de produtos
class CadastroProdutoDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Cadastrar Produto")
        self.setFixedSize(300, 300)

        layout = QFormLayout()
        self.codigo = QLineEdit()
        self.descricao = QLineEdit()
        self.quantidade = QLineEdit()
        self.preco_custo = QLineEdit()
        self.preco_venda = QLineEdit()
        self.estoque_minimo = QLineEdit()
        layout.addRow("Código:", self.codigo)
        layout.addRow("Descrição:", self.descricao)
        layout.addRow("Quantidade:", self.quantidade)
        layout.addRow("Preço Custo:", self.preco_custo)
        layout.addRow("Preço Venda:", self.preco_venda)
        layout.addRow("Estoque Mínimo:", self.estoque_minimo)

        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.salvar)
        layout.addWidget(btn_salvar)

        self.setLayout(layout)

    def salvar(self):
        try:
            codigo = self.codigo.text()
            descricao = self.descricao.text()
            quantidade = int(self.quantidade.text())
            preco_custo = float(self.preco_custo.text())
            preco_venda = float(self.preco_venda.text())
            estoque_minimo = int(self.estoque_minimo.text())
            if descricao and quantidade >= 0:
                self.db.cadastrar_produto(codigo, descricao, quantidade, preco_custo, preco_venda, estoque_minimo)
                QMessageBox.information(self, "Sucesso", "Produto cadastrado com sucesso!")
                self.accept()
            else:
                QMessageBox.warning(self, "Erro", "Descrição e quantidade válida são obrigatórios!")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Verifique os valores numéricos!")

# Janela para ordem de serviço
class OrdemServicoDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Nova Ordem de Serviço")
        self.setFixedSize(400, 400)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.cliente_combo = QComboBox()
        clientes = self.db.listar_clientes()
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])
        self.cliente_combo.currentIndexChanged.connect(self.atualizar_motos)
        form_layout.addRow("Cliente:", self.cliente_combo)

        self.moto_combo = QComboBox()
        form_layout.addRow("Moto:", self.moto_combo)

        self.descricao = QLineEdit()
        form_layout.addRow("Descrição:", self.descricao)

        self.produto_combo = QComboBox()
        produtos = self.db.listar_produtos()
        for produto in produtos:
            self.produto_combo.addItem(f"{produto[2]} ({produto[3]} un)", produto[0])
        form_layout.addRow("Peça:", self.produto_combo)

        self.quantidade_peca = QLineEdit()
        form_layout.addRow("Quantidade:", self.quantidade_peca)

        self.mao_obra = QLineEdit()
        form_layout.addRow("Mão de Obra (R$):", self.mao_obra)

        layout.addLayout(form_layout)

        btn_adicionar_peca = QPushButton("Adicionar Peça")
        btn_adicionar_peca.clicked.connect(self.adicionar_peca)
        layout.addWidget(btn_adicionar_peca)

        self.pecas_table = QTableWidget()
        self.pecas_table.setColumnCount(2)
        self.pecas_table.setHorizontalHeaderLabels(["Peça", "Quantidade"])
        layout.addWidget(self.pecas_table)

        btn_salvar = QPushButton("Concluir OS")
        btn_salvar.clicked.connect(self.salvar)
        layout.addWidget(btn_salvar)

        self.setLayout(layout)
        self.atualizar_motos()

    def atualizar_motos(self):
        self.moto_combo.clear()
        cliente_id = self.cliente_combo.currentData()
        motos = self.db.listar_motos(cliente_id)
        for moto in motos:
            self.moto_combo.addItem(f"{moto[1]} {moto[2]} ({moto[3]})", moto[0])

    def adicionar_peca(self):
        produto_id = self.produto_combo.currentData()
        try:
            quantidade = int(self.quantidade_peca.text())
            if quantidade > 0:
                produto = [p for p in self.db.listar_produtos() if p[0] == produto_id][0]
                row = self.pecas_table.rowCount()
                self.pecas_table.insertRow(row)
                self.pecas_table.setItem(row, 0, QTableWidgetItem(produto[2]))
                self.pecas_table.setItem(row, 1, QTableWidgetItem(str(quantidade)))
                self.quantidade_peca.clear()
            else:
                QMessageBox.warning(self, "Erro", "Quantidade deve ser maior que zero!")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Quantidade inválida!")

    def salvar(self):
        cliente_id = self.cliente_combo.currentData()
        moto_id = self.moto_combo.currentData()
        descricao = self.descricao.text()
        try:
            mao_obra = float(self.mao_obra.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Mão de obra inválida!")
            return

        if cliente_id and moto_id and descricao:
            os_id = self.db.criar_ordem_servico(cliente_id, moto_id, descricao)
            for row in range(self.pecas_table.rowCount()):
                produto_nome = self.pecas_table.item(row, 0).text()
                quantidade = int(self.pecas_table.item(row, 1).text())
                produto_id = [p[0] for p in self.db.listar_produtos() if p[2] == produto_nome][0]
                if not self.db.adicionar_peca_os(os_id, produto_id, quantidade):
                    QMessageBox.warning(self, "Erro", f"Estoque insuficiente para {produto_nome}!")
                    return
            self.db.concluir_os(os_id, mao_obra)
            total = self.db.calcular_total_os(os_id)
            QMessageBox.information(self, "Sucesso", f"OS concluída! Total: R${total:.2f}")
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios!")

# Janela para cadastro de motos
class CadastroMotoDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Cadastrar Moto")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog {background-color: #f5f5f5;}
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #2980b9;}
            QLabel {font-weight: bold;}
        """)

        # Dicionário de marcas e modelos
        self.marcas_modelos = {
            "Honda": ["CG 160", "Biz 125", "Pop 110i", "NXR 160 Bros", "XRE 190", "PCX 160", "CB 250 Twister", "CRF 230F"],
            "Yamaha": ["Factor 150", "XTZ Lander 250", "Crosser 150", "Fazer 150", "Fazer 250", "MT-03", "Neo 125", "Teneré 700", "Neo's (elétrica, lançamento)"],
            "Shineray": ["XY 125", "Jet 125SS", "SHI 175", "Urban 150", "Storm 250", "Iron 250", "Flash 150"],
            "Mottu": ["Sport 110i"],
            "Bajaj": ["Dominar 400", "Pulsar NS 200", "Pulsar N 160", "Pulsar N 200", "Platina 110"],
            "Avelloz": ["AZ1 50cc", "AZ 160 Xtreme"],
            "Royal Enfield": ["Classic 350", "Himalayan 450", "Interceptor 650", "Shotgun 650", "Bear 650"],
            "Dafra (parceira Sym/KYMCO)": ["ADX 150", "NHX 190", "Joyride 300"],
            "HaoJue (parceira Suzuki)": ["DR 150", "NK 150", "Lindy 125"],
            "BMW": ["G 310 R", "F 850 GS"],
            "Triumph": ["Tiger 900", "Speed Twin"],
            "Harley-Davidson": ["Iron 883"],
            "Kasinski": ["Comet 150"]
        }

        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.cliente_combo = QComboBox()
        clientes = self.db.listar_clientes()
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])
            
        self.marca_combo = QComboBox()
        self.marca_combo.addItem("Selecione uma marca...", "")
        for marca in sorted(self.marcas_modelos.keys()):
            self.marca_combo.addItem(marca, marca)
        self.marca_combo.currentTextChanged.connect(self.atualizar_modelos)
            
        self.modelo_combo = QComboBox()
        self.modelo_combo.addItem("Primeiro selecione uma marca", "")
        self.modelo_combo.setEnabled(False)
        
        self.placa = QLineEdit()
        self.placa.setPlaceholderText("ABC1234")
        
        self.ano = QLineEdit()
        self.ano.setPlaceholderText("2024")
        self.ano.setValidator(QIntValidator(1900, 2030))
        
        self.cor = QLineEdit()
        self.cor.setPlaceholderText("Preta")
        
        form_layout.addRow("Cliente:", self.cliente_combo)
        form_layout.addRow("Marca:", self.marca_combo)
        form_layout.addRow("Modelo:", self.modelo_combo)
        form_layout.addRow("Placa:", self.placa)
        form_layout.addRow("Ano:", self.ano)
        form_layout.addRow("Cor:", self.cor)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.salvar)
        btn_layout.addWidget(btn_salvar)
        
        layout.addSpacing(10)
        layout.addLayout(btn_layout)

    def atualizar_modelos(self, marca):
        self.modelo_combo.clear()
        if marca and marca in self.marcas_modelos:
            self.modelo_combo.addItem("Selecione um modelo...", "")
            for modelo in self.marcas_modelos[marca]:
                self.modelo_combo.addItem(modelo, modelo)
            self.modelo_combo.setEnabled(True)
        else:
            self.modelo_combo.addItem("Primeiro selecione uma marca", "")
            self.modelo_combo.setEnabled(False)

    def salvar(self):
        cliente_id = self.cliente_combo.currentData()
        marca = self.marca_combo.currentData()
        modelo = self.modelo_combo.currentData()
        placa = self.placa.text().strip().upper()
        ano = self.ano.text().strip()
        cor = self.cor.text().strip()
        
        if not cliente_id:
            QMessageBox.warning(self, "Erro", "Selecione um cliente!")
            return
            
        if not marca:
            QMessageBox.warning(self, "Erro", "Selecione uma marca!")
            return
            
        if not modelo:
            QMessageBox.warning(self, "Erro", "Selecione um modelo!")
            return
            
        if not placa:
            QMessageBox.warning(self, "Erro", "Placa é obrigatória!")
            return
            
        # Validação básica da placa (formato brasileiro)
        import re
        if not re.match(r'^[A-Z]{3}\d{4}$|^[A-Z]{3}\d[A-Z]\d{2}$', placa):
            QMessageBox.warning(self, "Erro", "Formato de placa inválido! Use formato ABC1234 ou ABC1D23")
            return
            
        self.db.cadastrar_moto(cliente_id, marca, modelo, placa, ano, cor)
        QMessageBox.information(self, "Sucesso", "Moto cadastrada com sucesso!")
        self.accept()

# Janela para venda de produtos
class VendaProdutosDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.produtos_selecionados = []
        self.setWindowTitle("Venda de Produtos")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {background-color: #f5f5f5;}
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #2980b9;}
            QLabel {font-weight: bold;}
            QTableWidget {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                background-color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        
        # Cliente
        cliente_layout = QHBoxLayout()
        cliente_layout.addWidget(QLabel("Cliente:"))
        self.cliente_combo = QComboBox()
        clientes = self.db.listar_clientes()
        self.cliente_combo.addItem("Cliente Avulso", 0)
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])
        cliente_layout.addWidget(self.cliente_combo, 1)
        layout.addLayout(cliente_layout)
        
        # Seleção de produtos
        produto_group = QGroupBox("Adicionar Produtos")
        produto_layout = QHBoxLayout()
        
        self.produto_combo = QComboBox()
        produtos = self.db.listar_produtos()
        for produto in produtos:
            self.produto_combo.addItem(f"{produto[2]} - R${produto[4]:.2f} ({produto[3]} em estoque)", produto[0])
        produto_layout.addWidget(self.produto_combo, 2)
        
        produto_layout.addWidget(QLabel("Qtd:"))
        self.quantidade = QLineEdit()
        self.quantidade.setFixedWidth(60)
        self.quantidade.setValidator(QIntValidator(1, 9999))
        produto_layout.addWidget(self.quantidade)
        
        btn_adicionar = QPushButton("Adicionar")
        btn_adicionar.clicked.connect(self.adicionar_produto)
        produto_layout.addWidget(btn_adicionar)
        
        produto_group.setLayout(produto_layout)
        layout.addWidget(produto_group)
        
        # Tabela de produtos selecionados
        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(5)
        self.tabela_produtos.setHorizontalHeaderLabels(["Código", "Produto", "Quantidade", "Valor Unit.", "Subtotal"])
        self.tabela_produtos.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabela_produtos)
        
        # Total
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("TOTAL:"))
        self.total_label = QLabel("R$ 0,00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        total_layout.addWidget(self.total_label)
        layout.addLayout(total_layout)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_remover = QPushButton("Remover Item")
        btn_remover.clicked.connect(self.remover_produto)
        btn_layout.addWidget(btn_remover)
        
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_finalizar = QPushButton("Finalizar Venda")
        btn_finalizar.clicked.connect(self.finalizar_venda)
        btn_finalizar.setStyleSheet("background-color: #27ae60; font-weight: bold;")
        btn_layout.addWidget(btn_finalizar)
        
        layout.addLayout(btn_layout)

    def adicionar_produto(self):
        produto_id = self.produto_combo.currentData()
        produto_texto = self.produto_combo.currentText()
        
        try:
            quantidade = int(self.quantidade.text())
            if quantidade <= 0:
                QMessageBox.warning(self, "Erro", "Quantidade deve ser maior que zero!")
                return
                
            # Obtendo informações do produto
            produtos = self.db.listar_produtos()
            produto = next(p for p in produtos if p[0] == produto_id)
            
            if quantidade > produto[3]:
                QMessageBox.warning(self, "Erro", f"Estoque insuficiente! Disponível: {produto[3]}")
                return
                
            codigo = produto[1]
            nome = produto[2]
            preco = produto[4]
            subtotal = preco * quantidade
            
            # Adicionar à tabela
            row = self.tabela_produtos.rowCount()
            self.tabela_produtos.insertRow(row)
            self.tabela_produtos.setItem(row, 0, QTableWidgetItem(codigo))
            self.tabela_produtos.setItem(row, 1, QTableWidgetItem(nome))
            self.tabela_produtos.setItem(row, 2, QTableWidgetItem(str(quantidade)))
            self.tabela_produtos.setItem(row, 3, QTableWidgetItem(f"R$ {preco:.2f}"))
            self.tabela_produtos.setItem(row, 4, QTableWidgetItem(f"R$ {subtotal:.2f}"))
            
            # Adicionar à lista de produtos
            self.produtos_selecionados.append((produto_id, quantidade, preco))
            
            # Atualizar total
            self.atualizar_total()
            self.quantidade.clear()
            
        except ValueError:
            QMessageBox.warning(self, "Erro", "Quantidade inválida!")

    def remover_produto(self):
        selected_row = self.tabela_produtos.currentRow()
        if selected_row >= 0:
            self.tabela_produtos.removeRow(selected_row)
            self.produtos_selecionados.pop(selected_row)
            self.atualizar_total()
        else:
            QMessageBox.warning(self, "Aviso", "Selecione um produto para remover!")

    def atualizar_total(self):
        total = sum(quantidade * preco for _, quantidade, preco in self.produtos_selecionados)
        self.total_label.setText(f"R$ {total:.2f}")

    def finalizar_venda(self):
        if not self.produtos_selecionados:
            QMessageBox.warning(self, "Erro", "Adicione pelo menos um produto para finalizar a venda!")
            return
            
        cliente_id = self.cliente_combo.currentData()
        
        # Preparar dados para registro
        produtos_quantidades = [(produto_id, quantidade) for produto_id, quantidade, _ in self.produtos_selecionados]
        total = self.db.registrar_venda(cliente_id, produtos_quantidades)
        
        if total is not None:
            QMessageBox.information(self, "Sucesso", f"Venda finalizada com sucesso!\nTotal: R$ {total:.2f}")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Erro ao finalizar venda. Verifique o estoque!")

# Janela para cadastro de funcionários
class CadastroFuncionarioDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Cadastrar Funcionário")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog {background-color: #f5f5f5;}
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #2980b9;}
            QLabel {font-weight: bold;}
        """)

        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome completo")
        
        self.cpf = QLineEdit()
        self.cpf.setPlaceholderText("000.000.000-00")
        
        self.telefone = QLineEdit()
        self.telefone.setPlaceholderText("11999999999")
        telefone_validator = QRegExpValidator(QRegExp(r'\d{0,11}'))
        self.telefone.setValidator(telefone_validator)
        
        self.funcao_combo = QComboBox()
        self.funcao_combo.addItem("Selecione uma função...", "")
        funcoes = ["Administrador", "Mecânico", "Serviços Gerais", "Vendas"]
        for funcao in funcoes:
            self.funcao_combo.addItem(funcao, funcao)
        
        self.data_admissao = QLineEdit()
        self.data_admissao.setPlaceholderText("DD/MM/AAAA")
        
        self.salario = QLineEdit()
        self.salario.setPlaceholderText("0.00")
        salario_validator = QRegExpValidator(QRegExp(r'\d*\.?\d{0,2}'))
        self.salario.setValidator(salario_validator)
        
        form_layout.addRow("Nome:", self.nome)
        form_layout.addRow("CPF:", self.cpf)
        form_layout.addRow("Telefone (11 dígitos):", self.telefone)
        form_layout.addRow("Função:", self.funcao_combo)
        form_layout.addRow("Data Admissão:", self.data_admissao)
        form_layout.addRow("Salário (R$):", self.salario)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.salvar)
        btn_layout.addWidget(btn_salvar)
        
        layout.addSpacing(10)
        layout.addLayout(btn_layout)

    def salvar(self):
        nome = self.nome.text().strip()
        cpf = self.cpf.text().strip()
        telefone = self.telefone.text().strip()
        funcao = self.funcao_combo.currentData()
        data_admissao = self.data_admissao.text().strip()
        salario_text = self.salario.text().strip()
        
        if not nome:
            QMessageBox.warning(self, "Erro", "Nome é obrigatório!")
            return
            
        if not funcao:
            QMessageBox.warning(self, "Erro", "Selecione uma função!")
            return
            
        if cpf and len(cpf.replace(".", "").replace("-", "")) != 11:
            QMessageBox.warning(self, "Erro", "CPF deve ter 11 dígitos!")
            return
            
        if telefone and len(telefone) != 11:
            QMessageBox.warning(self, "Erro", "Telefone deve ter 11 dígitos!")
            return
            
        try:
            salario = float(salario_text) if salario_text else 0.0
        except ValueError:
            QMessageBox.warning(self, "Erro", "Salário deve ser um valor numérico!")
            return
            
        funcionario_id = self.db.cadastrar_funcionario(nome, cpf, telefone, funcao, data_admissao, salario)
        
        if funcionario_id is None:
            QMessageBox.warning(self, "Erro", "CPF já cadastrado!")
            return
            
        QMessageBox.information(self, "Sucesso", "Funcionário cadastrado com sucesso!")
        self.accept()

# Janela principal
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Sistema de Gestão - Oficina de Motos")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {background-color: #f5f5f5;}
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {background-color: #2980b9;}
            QTableWidget {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                background-color: #ffffff;
                gridline-color: #e0e0e0;
            }
            QTableWidget QHeaderView::section {
                background-color: #3498db;
                padding: 8px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 0px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Título e imagem do sistema
        header_layout = QHBoxLayout()
        logo_label = QLabel("SISTEMA DE GESTÃO - OFICINA DE MOTOS")
        logo_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Layout principal dividido em duas partes
        content_layout = QHBoxLayout()
        
        # Painel de botões à esquerda
        button_panel = QWidget()
        button_panel.setFixedWidth(300)
        button_panel.setStyleSheet("background-color: #2c3e50; border-radius: 10px;")
        button_layout = QVBoxLayout(button_panel)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(15, 25, 15, 25)
        
        # Título do painel
        panel_title = QLabel("CONTROLES")
        panel_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        panel_title.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(panel_title)
        button_layout.addSpacing(15)
        
        # Categorias de botões
        categories = {
            "Cadastros": [
                ("Cadastrar Cliente", self.cadastrar_cliente),
                ("Cadastrar Moto", self.cadastrar_moto),
                ("Cadastrar Produto", self.cadastrar_produto)
            ],
            "Funcionários": [
                ("Cadastrar Funcionário", self.cadastrar_funcionario),
                ("Listar Funcionários", self.listar_funcionarios)
            ],
            "Operações": [
                ("Nova Ordem de Serviço", self.nova_os),
                ("Vender Produtos", self.vender_produtos)
            ],
            "Relatórios": [
                ("Ordens de Serviço", self.listar_os),
                ("Estoque Baixo", self.relatorio_estoque),
                ("Vendas", self.relatorio_vendas)
            ]
        }
        
        for category, buttons in categories.items():
            cat_label = QLabel(category)
            cat_label.setStyleSheet("color: #3498db; font-size: 16px; font-weight: bold; margin-top: 10px;")
            button_layout.addWidget(cat_label)
            
            for btn_text, btn_function in buttons:
                btn = QPushButton(btn_text)
                btn.clicked.connect(btn_function)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34495e;
                        color: white;
                        text-align: left;
                        padding: 18px 25px;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: bold;
                        margin-left: 10px;
                        margin-right: 10px;
                    }
                    QPushButton:hover {
                        background-color: #3498db;
                    }
                """)
                button_layout.addWidget(btn)
            
            button_layout.addSpacing(15)
        
        button_layout.addStretch()
        
        # Área de conteúdo à direita
        content_area = QWidget()
        content_layout_right = QVBoxLayout(content_area)
        
        # Barra de pesquisa
        search_layout = QHBoxLayout()
        search_label = QLabel("Pesquisar:")
        search_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para pesquisar...")
        self.search_input.setStyleSheet("padding: 10px; border-radius: 5px; border: 1px solid #ddd; font-size: 14px;")
        search_button = QPushButton("Buscar")
        search_button.setStyleSheet("font-size: 14px; padding: 10px 20px;")
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(search_button)
        
        content_layout_right.addLayout(search_layout)
        
        # Status atual
        self.status_label = QLabel("Bem-vindo ao Sistema de Gestão de Oficina")
        self.status_label.setStyleSheet("color: #555; font-size: 16px; margin-top: 10px; font-weight: bold;")
        content_layout_right.addWidget(self.status_label)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        content_layout_right.addWidget(self.table)
        
        # Botões de ação para o item selecionado
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.setStyleSheet("font-size: 14px; padding: 12px 25px; background-color: #f39c12; color: white; font-weight: bold;")
        self.edit_btn.clicked.connect(self.edit_selected)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Excluir")
        self.delete_btn.setStyleSheet("font-size: 14px; padding: 12px 25px; background-color: #e74c3c; color: white; font-weight: bold;")
        self.delete_btn.clicked.connect(self.delete_selected)
        action_layout.addWidget(self.delete_btn)
        
        content_layout_right.addLayout(action_layout)
        
        # Adicionando os painéis ao layout principal
        content_layout.addWidget(button_panel)
        content_layout.addWidget(content_area, 1)
        
        main_layout.addLayout(content_layout, 1)
        
        # Barra de status no rodapé
        self.statusBar().showMessage("Sistema iniciado " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
        # Inicialmente mostrar lista de OS
        self.listar_os()

    # Métodos adicionais para novas funcionalidades
    def cadastrar_cliente(self):
        dialog = CadastroClienteDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.status_label.setText("Cliente cadastrado com sucesso!")
            self.listar_clientes()  # Atualiza a tabela se estiver na visualização de clientes
    
    def cadastrar_produto(self):
        dialog = CadastroProdutoDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.status_label.setText("Produto cadastrado com sucesso!")
            self.listar_produtos()  # Atualiza a tabela se estiver na visualização de produtos
    
    def cadastrar_moto(self):
        dialog = CadastroMotoDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.status_label.setText("Moto cadastrada com sucesso!")
            # Atualiza a tabela se estiver mostrando motos de um cliente específico
            self._atualizar_visualizacao_atual()
    
    def cadastrar_funcionario(self):
        dialog = CadastroFuncionarioDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.status_label.setText("Funcionário cadastrado com sucesso!")
            self.listar_funcionarios()  # Atualiza a tabela se estiver na visualização de funcionários
    
    def nova_os(self):
        dialog = OrdemServicoDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.status_label.setText("Ordem de serviço registrada com sucesso!")
            self.listar_os()  # Atualiza a tabela de OS
    
    def vender_produtos(self):
        dialog = VendaProdutosDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.status_label.setText("Venda registrada com sucesso!")
            # Pode afetar o estoque de produtos
            if self.status_label.text().startswith("Lista de Produtos"):
                self.listar_produtos()
    
    def listar_os(self):
        self.status_label.setText("Ordens de Serviço")
        self.table.clear()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Cliente", "Moto", "Descrição", "Status", "Data"])
        
        ordens = self.db.listar_os()
        self.table.setRowCount(len(ordens))
        
        for i, ordem in enumerate(ordens):
            for j, value in enumerate(ordem):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
                
        self.table.resizeColumnsToContents()
    
    def relatorio_estoque(self):
        self.status_label.setText("Relatório de Estoque Baixo")
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Código", "Descrição", "Quantidade"])
        
        produtos = self.db.relatorio_estoque_baixo()
        self.table.setRowCount(len(produtos))
        
        for i, produto in enumerate(produtos):
            for j, value in enumerate(produto):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
                
        self.table.resizeColumnsToContents()
    
    def relatorio_vendas(self):
        self.status_label.setText("Relatório de Vendas")
        self.table.clear()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Cliente", "Data", "Total"])
        
        self.cursor = self.db.conn.cursor()
        self.cursor.execute("""
            SELECT v.id, COALESCE(c.nome, 'Cliente Avulso'), v.data,
                   (SELECT SUM(p.preco_venda * vi.quantidade)
                    FROM venda_itens vi
                    JOIN produtos p ON vi.produto_id = p.id
                    WHERE vi.venda_id = v.id) as total
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            ORDER BY v.data DESC
        """)
        
        vendas = self.cursor.fetchall()
        
        self.table.setRowCount(len(vendas))
        for i, venda in enumerate(vendas):
            for j, value in enumerate(venda):
                if j == 3 and value is not None:  # Formatar o valor total
                    text = f"R$ {value:.2f}"
                else:
                    text = str(value) if value is not None else ""
                self.table.setItem(i, j, QTableWidgetItem(text))
                
        self.table.resizeColumnsToContents()
    
    def listar_produtos(self):
        self.status_label.setText("Lista de Produtos")
        self.table.clear()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Código", "Descrição", "Estoque", "Preço Venda"])
        
        produtos = self.db.listar_produtos()
        self.table.setRowCount(len(produtos))
        
        for i, produto in enumerate(produtos):
            for j, value in enumerate(produto):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
                
        self.table.resizeColumnsToContents()
    
    def listar_clientes(self):
        self.status_label.setText("Lista de Clientes")
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Telefone"])
        
        self.cursor = self.db.conn.cursor()
        self.cursor.execute("SELECT id, nome, telefone FROM clientes")
        clientes = self.cursor.fetchall()
        
        self.table.setRowCount(len(clientes))
        for i, cliente in enumerate(clientes):
            for j, value in enumerate(cliente):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
                
        self.table.resizeColumnsToContents()
    
    def listar_funcionarios(self):
        self.status_label.setText("Lista de Funcionários")
        self.table.clear()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Função", "Status"])
        
        funcionarios = self.db.listar_funcionarios()
        
        self.table.setRowCount(len(funcionarios))
        for i, funcionario in enumerate(funcionarios):
            for j, value in enumerate(funcionario):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
                
        self.table.resizeColumnsToContents()
    
    def search(self):
        query = self.search_input.text().strip().lower()
        self.status_label.setText(f"Pesquisando por: {query}")
        
        # Implementação básica - filtra itens mostrados na tabela atual
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            
            self.table.setRowHidden(row, not match)
    
    def edit_selected(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            item_id = self.table.item(selected_row, 0).text()
            self.status_label.setText(f"Editando item {item_id}...")
            # Aqui você implementaria a edição com base no tipo de dados atual
            QMessageBox.information(self, "Informação", "Funcionalidade de edição em desenvolvimento.")
        else:
            QMessageBox.warning(self, "Aviso", "Selecione um item para editar!")
    
    def delete_selected(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            item_id = self.table.item(selected_row, 0).text()
            item_nome = self.table.item(selected_row, 1).text() if self.table.columnCount() > 1 else ""
            
            # Identificar o tipo de item baseado no status atual
            texto_status = self.status_label.text()
            
            if texto_status.startswith("Lista de Clientes"):
                reply = QMessageBox.question(self, 'Confirmar Exclusão', 
                                            f"Tem certeza que deseja excluir o cliente '{item_nome}' (ID: {item_id})?\n\n"
                                            "Esta ação não pode ser desfeita.",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    sucesso, mensagem = self.db.excluir_cliente(int(item_id))
                    if sucesso:
                        QMessageBox.information(self, "Sucesso", mensagem)
                        self.status_label.setText("Cliente excluído com sucesso!")
                        self.listar_clientes()  # Atualiza a lista
                    else:
                        QMessageBox.warning(self, "Erro", mensagem)
                        
            elif texto_status.startswith("Lista de Funcionários"):
                reply = QMessageBox.question(self, 'Confirmar Exclusão', 
                                            f"Tem certeza que deseja excluir o funcionário '{item_nome}' (ID: {item_id})?\n\n"
                                            "Esta ação não pode ser desfeita.",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    sucesso, mensagem = self.db.excluir_funcionario(int(item_id))
                    if sucesso:
                        QMessageBox.information(self, "Sucesso", mensagem)
                        self.status_label.setText("Funcionário excluído com sucesso!")
                        self.listar_funcionarios()  # Atualiza a lista
                    else:
                        QMessageBox.warning(self, "Erro", mensagem)
                        
            elif texto_status.startswith("Lista de Produtos"):
                # Implementar exclusão de produtos futuramente
                QMessageBox.information(self, "Informação", "Funcionalidade de exclusão de produtos em desenvolvimento.")
                
            elif texto_status.startswith("Ordens de Serviço"):
                # Implementar exclusão de OS futuramente
                QMessageBox.information(self, "Informação", "Funcionalidade de exclusão de ordens de serviço em desenvolvimento.")
                
            else:
                QMessageBox.warning(self, "Aviso", "Tipo de item não identificado para exclusão.")
        else:
            QMessageBox.warning(self, "Aviso", "Selecione um item para excluir!")

    def _atualizar_visualizacao_atual(self):
        """Atualiza a visualização atual com base no status_label"""
        texto = self.status_label.text()
        if texto.startswith("Lista de Clientes"):
            self.listar_clientes()
        elif texto.startswith("Lista de Funcionários"):
            self.listar_funcionarios()
        elif texto.startswith("Lista de Produtos"):
            self.listar_produtos()
        elif texto.startswith("Ordens de Serviço"):
            self.listar_os()
        elif texto.startswith("Relatório de Estoque"):
            self.relatorio_estoque()
        elif texto.startswith("Relatório de Vendas"):
            self.relatorio_vendas()
        # Se não corresponder a nenhuma visualização conhecida, não faz nada

# Inicialização
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    
    # Aplicar estilo global
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())