
import os
from datetime import datetime, date
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify, abort
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

# ==================================================
# CONFIGURAÇÕES DA APLICAÇÃO
# ==================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "medcontrol-chave-desenvolvimento"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "medcontrol.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

STATUS_VALIDOS = [
    "Agendada",
    "Concluída",
    "Cancelada"
]


# Ativar chaves estrangeiras no SQLite
@event.listens_for(Engine, "connect")
def ativar_chaves_estrangeiras(conexao, registro):
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ==================================================
# MODELOS DO BANCO DE DADOS
# ==================================================

class Paciente(db.Model):

    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), nullable=False)

    consultas = db.relationship(
        "Consulta",
        back_populates="paciente",
        passive_deletes=True
    )


class Medico(db.Model):

    __tablename__ = "medicos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    especialidade = db.Column(db.String(100), nullable=False)
    crm = db.Column(db.String(30), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

    consultas = db.relationship(
        "Consulta",
        back_populates="medico",
        passive_deletes=True
    )


class Consulta(db.Model):

    __tablename__ = "consultas"

    id = db.Column(db.Integer, primary_key=True)

    paciente_id = db.Column(
        db.Integer,
        db.ForeignKey("pacientes.id", ondelete="RESTRICT"),
        nullable=False
    )

    medico_id = db.Column(
        db.Integer,
        db.ForeignKey("medicos.id", ondelete="RESTRICT"),
        nullable=False
    )

    data = db.Column(db.Date, nullable=False)
    horario = db.Column(db.Time, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Agendada"
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="consultas"
    )

    medico = db.relationship(
        "Medico",
        back_populates="consultas"
    )


# ==================================================
# UC30 - LÓGICA DE PROGRAMAÇÃO
# ALGORITMO DE ORDENAÇÃO BUBBLE SORT
# ==================================================

def ordenar_pacientes(pacientes):

    lista = list(pacientes)
    tamanho = len(lista)

    for i in range(tamanho - 1):

        trocou = False

        for j in range(tamanho - i - 1):

            if lista[j].nome.casefold() > lista[j + 1].nome.casefold():

                lista[j], lista[j + 1] = (
                    lista[j + 1], lista[j]
                )

                trocou = True

        if not trocou:
            break

    return lista


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def salvar_banco():

    try:
        db.session.commit()
        return True

    except IntegrityError:
        db.session.rollback()

        flash(
            "Não foi possível concluir a operação. "
            "Verifique os dados informados.",
            "danger"
        )

        return False


def validar_paciente(formulario):

    nome = formulario.get("nome", "").strip()
    telefone = formulario.get("telefone", "").strip()
    email = formulario.get("email", "").strip()

    if not nome or not telefone or not email:
        raise ValueError("Preencha todos os campos.")

    nascimento = datetime.strptime(
        formulario.get("data_nascimento", ""),
        "%Y-%m-%d"
    ).date()

    if nascimento > date.today():
        raise ValueError("Data de nascimento inválida.")

    if "@" not in email:
        raise ValueError("Informe um e-mail válido.")

    return {
        "nome": nome,
        "data_nascimento": nascimento,
        "telefone": telefone,
        "email": email
    }


def validar_medico(formulario, medico_id=None):

    dados = {
        "nome": formulario.get("nome", "").strip(),
        "especialidade": formulario.get(
            "especialidade", ""
        ).strip(),
        "crm": formulario.get("crm", "").strip().upper(),
        "telefone": formulario.get("telefone", "").strip()
    }

    if not all(dados.values()):
        raise ValueError("Preencha todos os campos.")

    busca = Medico.query.filter_by(crm=dados["crm"])

    if medico_id is not None:
        busca = busca.filter(Medico.id != medico_id)

    if busca.first():
        raise ValueError("Este CRM já está cadastrado.")

    return dados


def validar_consulta(formulario, consulta_id=None):

    paciente_id = int(formulario.get("paciente_id", ""))
    medico_id = int(formulario.get("medico_id", ""))

    data_consulta = datetime.strptime(
        formulario.get("data", ""),
        "%Y-%m-%d"
    ).date()

    horario = datetime.strptime(
        formulario.get("horario", ""),
        "%H:%M"
    ).time()

    status = formulario.get("status", "Agendada")

    if status not in STATUS_VALIDOS:
        raise ValueError("Status inválido.")

    if not db.session.get(Paciente, paciente_id):
        raise ValueError("Paciente não encontrado.")

    if not db.session.get(Medico, medico_id):
        raise ValueError("Médico não encontrado.")

    if status == "Agendada":

        if datetime.combine(
            data_consulta, horario
        ) < datetime.now():

            raise ValueError(
                "Não é possível agendar consultas no passado."
            )

        conflito = Consulta.query.filter(
            Consulta.data == data_consulta,
            Consulta.horario == horario,
            Consulta.status == "Agendada",
            db.or_(
                Consulta.medico_id == medico_id,
                Consulta.paciente_id == paciente_id
            )
        )

        if consulta_id is not None:
            conflito = conflito.filter(
                Consulta.id != consulta_id
            )

        if conflito.first():
            raise ValueError(
                "O médico ou paciente já possui "
                "uma consulta neste horário."
            )

    return {
        "paciente_id": paciente_id,
        "medico_id": medico_id,
        "data": data_consulta,
        "horario": horario,
        "status": status
    }


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/")
def index():

    total_pacientes = Paciente.query.count()
    total_medicos = Medico.query.count()
    total_consultas = Consulta.query.count()

    agendadas = Consulta.query.filter_by(
        status="Agendada"
    ).count()

    concluidas = Consulta.query.filter_by(
        status="Concluída"
    ).count()

    canceladas = Consulta.query.filter_by(
        status="Cancelada"
    ).count()

    consultas_hoje = Consulta.query.filter_by(
        data=date.today(),
        status="Agendada"
    ).count()

    proximas_consultas = (
        Consulta.query
        .join(Paciente)
        .join(Medico)
        .filter(
            Consulta.status == "Agendada",
            Consulta.data >= date.today()
        )
        .order_by(
            Consulta.data.asc(),
            Consulta.horario.asc()
        )
        .limit(5)
        .all()
    )

    return render_template(
        "index.html",
        total_pacientes=total_pacientes,
        total_medicos=total_medicos,
        total_consultas=total_consultas,
        agendadas=agendadas,
        concluidas=concluidas,
        canceladas=canceladas,
        consultas_hoje=consultas_hoje,
        proximas_consultas=proximas_consultas
    )


# ==================================================
# CRUD DE PACIENTES
# ==================================================

@app.route("/pacientes")
def pacientes():

    pesquisa = request.args.get("pesquisa", "").strip()

    consulta = Paciente.query

    # WHERE
    if pesquisa:
        consulta = consulta.filter(
            Paciente.nome.ilike(f"%{pesquisa}%")
        )

    lista = consulta.all()

    # Ordenação utilizando Bubble Sort
    lista = ordenar_pacientes(lista)

    return render_template(
        "pacientes.html",
        pacientes=lista,
        pesquisa=pesquisa
    )


@app.route("/pacientes/novo", methods=["GET", "POST"])
def novo_paciente():

    if request.method == "POST":

        try:
            dados = validar_paciente(request.form)

            paciente = Paciente(**dados)

            db.session.add(paciente)

            if salvar_banco():
                flash("Paciente cadastrado com sucesso!", "success")
                return redirect(url_for("pacientes"))

        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "form_paciente.html",
        paciente=None
    )


@app.route(
    "/pacientes/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_paciente(id):

    paciente = db.get_or_404(Paciente, id)

    if request.method == "POST":

        try:
            dados = validar_paciente(request.form)

            for campo, valor in dados.items():
                setattr(paciente, campo, valor)

            if salvar_banco():
                flash("Paciente atualizado com sucesso!", "success")
                return redirect(url_for("pacientes"))

        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "form_paciente.html",
        paciente=paciente
    )


@app.route("/pacientes/excluir/<int:id>", methods=["POST"])
def excluir_paciente(id):

    paciente = db.get_or_404(Paciente, id)

    if paciente.consultas:

        flash(
            "Não é possível excluir um paciente "
            "que possui consultas vinculadas.",
            "warning"
        )

    else:

        db.session.delete(paciente)

        if salvar_banco():
            flash("Paciente excluído com sucesso!", "success")

    return redirect(url_for("pacientes"))


# ==================================================
# CRUD DE MÉDICOS
# ==================================================

@app.route("/medicos")
def medicos():

    pesquisa = request.args.get("pesquisa", "").strip()

    consulta = Medico.query

    if pesquisa:

        consulta = consulta.filter(
            db.or_(
                Medico.nome.ilike(f"%{pesquisa}%"),
                Medico.especialidade.ilike(f"%{pesquisa}%"),
                Medico.crm.ilike(f"%{pesquisa}%")
            )
        )

    # ORDER BY
    lista = consulta.order_by(Medico.nome.asc()).all()

    return render_template(
        "medicos.html",
        medicos=lista,
        pesquisa=pesquisa
    )


@app.route("/medicos/novo", methods=["GET", "POST"])
def novo_medico():

    if request.method == "POST":

        try:
            dados = validar_medico(request.form)

            medico = Medico(**dados)

            db.session.add(medico)

            if salvar_banco():
                flash("Médico cadastrado com sucesso!", "success")
                return redirect(url_for("medicos"))

        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "form_medico.html",
        medico=None
    )


@app.route(
    "/medicos/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_medico(id):

    medico = db.get_or_404(Medico, id)

    if request.method == "POST":

        try:
            dados = validar_medico(request.form, medico.id)

            for campo, valor in dados.items():
                setattr(medico, campo, valor)

            if salvar_banco():
                flash("Médico atualizado com sucesso!", "success")
                return redirect(url_for("medicos"))

        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "form_medico.html",
        medico=medico
    )


@app.route("/medicos/excluir/<int:id>", methods=["POST"])
def excluir_medico(id):

    medico = db.get_or_404(Medico, id)

    if medico.consultas:

        flash(
            "Não é possível excluir um médico "
            "que possui consultas vinculadas.",
            "warning"
        )

    else:

        db.session.delete(medico)

        if salvar_banco():
            flash("Médico excluído com sucesso!", "success")

    return redirect(url_for("medicos"))


# ==================================================
# CRUD DE CONSULTAS
# ==================================================

@app.route("/consultas")
def consultas():

    medico_id = request.args.get("medico_id", type=int)
    data_filtro = request.args.get("data", "")
    status = request.args.get("status", "")

    # JOIN
    consulta = Consulta.query.join(Paciente).join(Medico)

    # WHERE
    if medico_id:
        consulta = consulta.filter(
            Consulta.medico_id == medico_id
        )

    if data_filtro:

        try:
            data_convertida = datetime.strptime(
                data_filtro, "%Y-%m-%d"
            ).date()

            consulta = consulta.filter(
                Consulta.data == data_convertida
            )

        except ValueError:
            flash("Data de filtro inválida.", "warning")

    if status in STATUS_VALIDOS:
        consulta = consulta.filter(
            Consulta.status == status
        )

    # ORDER BY
    lista = consulta.order_by(
        Consulta.data.desc(),
        Consulta.horario.desc()
    ).all()

    lista_medicos = Medico.query.order_by(
        Medico.nome.asc()
    ).all()

    return render_template(
        "consultas.html",
        consultas=lista,
        medicos=lista_medicos,
        medico_id=medico_id,
        data_filtro=data_filtro,
        status=status,
        status_validos=STATUS_VALIDOS
    )


@app.route("/consultas/nova", methods=["GET", "POST"])
def nova_consulta():

    if request.method == "POST":

        try:
            dados = validar_consulta(request.form)

            consulta = Consulta(**dados)

            db.session.add(consulta)

            if salvar_banco():
                flash("Consulta agendada com sucesso!", "success")
                return redirect(url_for("consultas"))

        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "form_consulta.html",
        consulta=None,
        pacientes=ordenar_pacientes(Paciente.query.all()),
        medicos=Medico.query.order_by(Medico.nome.asc()).all(),
        status_validos=STATUS_VALIDOS
    )


@app.route(
    "/consultas/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_consulta(id):

    consulta = db.get_or_404(Consulta, id)

    if request.method == "POST":

        try:
            dados = validar_consulta(
                request.form, consulta.id
            )

            for campo, valor in dados.items():
                setattr(consulta, campo, valor)

            if salvar_banco():
                flash("Consulta atualizada com sucesso!", "success")
                return redirect(url_for("consultas"))

        except ValueError as erro:
            flash(str(erro), "danger")

    return render_template(
        "form_consulta.html",
        consulta=consulta,
        pacientes=ordenar_pacientes(Paciente.query.all()),
        medicos=Medico.query.order_by(Medico.nome.asc()).all(),
        status_validos=STATUS_VALIDOS
    )


@app.route("/consultas/excluir/<int:id>", methods=["POST"])
def excluir_consulta(id):

    consulta = db.get_or_404(Consulta, id)

    db.session.delete(consulta)

    if salvar_banco():
        flash("Consulta excluída com sucesso!", "success")

    return redirect(url_for("consultas"))


@app.route("/consultas/status/<int:id>", methods=["POST"])
def alterar_status(id):

    consulta = db.get_or_404(Consulta, id)

    novo_status = request.form.get("status", "")

    if novo_status not in STATUS_VALIDOS:
        abort(400)

    try:

        dados = {
            "paciente_id": consulta.paciente_id,
            "medico_id": consulta.medico_id,
            "data": consulta.data.isoformat(),
            "horario": consulta.horario.strftime("%H:%M"),
            "status": novo_status
        }

        validar_consulta(dados, consulta.id)

        consulta.status = novo_status

        if salvar_banco():
            flash("Status atualizado com sucesso!", "success")

    except ValueError as erro:
        flash(str(erro), "danger")

    return redirect(url_for("consultas"))


# ==================================================
# UC33 - API REST / JSON
# ==================================================

@app.route("/api/pacientes")
def api_pacientes():

    lista = ordenar_pacientes(Paciente.query.all())

    resultado = []

    for paciente in lista:

        resultado.append({
            "id": paciente.id,
            "nome": paciente.nome
        })

    return jsonify(resultado)


@app.route("/api/medicos")
def api_medicos():

    lista = Medico.query.order_by(Medico.nome.asc()).all()

    resultado = []

    for medico in lista:

        resultado.append({
            "id": medico.id,
            "nome": medico.nome,
            "especialidade": medico.especialidade
        })

    return jsonify(resultado)


@app.route("/api/consultas")
def api_consultas():

    lista = (
        Consulta.query
        .join(Paciente)
        .join(Medico)
        .order_by(Consulta.data.asc())
        .all()
    )

    resultado = []

    for consulta in lista:

        resultado.append({
            "id": consulta.id,
            "paciente_id": consulta.paciente_id,
            "medico": consulta.medico.nome,
            "especialidade": consulta.medico.especialidade,
            "data": consulta.data.strftime("%d/%m/%Y"),
            "horario": consulta.horario.strftime("%H:%M"),
            "status": consulta.status
        })

    return jsonify(resultado)


@app.route("/api/dashboard")
def api_dashboard():

    return jsonify({
        "pacientes": Paciente.query.count(),
        "medicos": Medico.query.count(),
        "consultas": Consulta.query.count(),
        "agendadas": Consulta.query.filter_by(
            status="Agendada"
        ).count(),
        "concluidas": Consulta.query.filter_by(
            status="Concluída"
        ).count(),
        "canceladas": Consulta.query.filter_by(
            status="Cancelada"
        ).count()
    })


# ==================================================
# TRATAMENTO DE ERROS
# ==================================================

@app.errorhandler(404)
def pagina_nao_encontrada(erro):

    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
