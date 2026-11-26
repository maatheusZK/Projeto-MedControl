
/* ==================================================
   MEDCONTROL — SISTEMA DE GESTÃO CLÍNICA
   JavaScript principal
================================================== */

"use strict";


/* ==================================================
   01. INICIALIZAÇÃO DO SISTEMA
================================================== */

document.addEventListener("DOMContentLoaded", () => {

    inicializarTema();
    inicializarMenu();
    atualizarData();
    atualizarAno();
    inicializarAlertas();
    inicializarMascaras();
    inicializarExclusoes();
    inicializarValidacoes();
    inicializarResumoConsulta();
    inicializarFormularios();
    inicializarStatus();

    atualizarIcones();

});


/* ==================================================
   02. ÍCONES LUCIDE
================================================== */

function atualizarIcones() {

    if (typeof lucide !== "undefined") {

        lucide.createIcons();

    }

}


/* ==================================================
   03. MODO CLARO E ESCURO
================================================== */

function inicializarTema() {

    const botaoTema = document.getElementById("theme-toggle");

    let temaSalvo = null;

    try {

        temaSalvo = localStorage.getItem("medcontrol-theme");

    } catch (erro) {

        console.warn("Não foi possível recuperar o tema.");

    }

    const temaInicial = ["light", "dark"].includes(temaSalvo)
        ? temaSalvo
        : "light";

    aplicarTema(temaInicial);

    if (!botaoTema) return;

    botaoTema.addEventListener("click", () => {

        const temaAtual =
            document.documentElement.getAttribute("data-theme");

        const novoTema = temaAtual === "dark"
            ? "light"
            : "dark";

        aplicarTema(novoTema);

        try {

            localStorage.setItem("medcontrol-theme", novoTema);

        } catch (erro) {

            console.warn("Não foi possível salvar o tema.");

        }

    });

}


function aplicarTema(tema) {

    document.documentElement.setAttribute("data-theme", tema);

    const botaoTema = document.getElementById("theme-toggle");
    const iconeTema = document.getElementById("theme-icon");

    const temaEscuro = tema === "dark";

    if (iconeTema) {

        const novoIcone = document.createElement("i");

        novoIcone.id = "theme-icon";

        novoIcone.setAttribute(
            "data-lucide",
            temaEscuro ? "sun" : "moon"
        );

        iconeTema.replaceWith(novoIcone);

    }

    if (botaoTema) {

        const mensagem = temaEscuro
            ? "Ativar modo claro"
            : "Ativar modo escuro";

        botaoTema.title = mensagem;

        botaoTema.setAttribute("aria-label", mensagem);

        botaoTema.setAttribute(
            "aria-pressed",
            String(temaEscuro)
        );

    }

    atualizarIcones();

}


/* ==================================================
   04. MENU LATERAL RESPONSIVO
================================================== */

function inicializarMenu() {

    const sidebar = document.getElementById("sidebar");

    const overlay = document.getElementById("sidebar-overlay");

    const botaoMenu = document.getElementById("menu-toggle");

    if (!sidebar || !overlay || !botaoMenu) return;

    botaoMenu.setAttribute("aria-controls", "sidebar");
    botaoMenu.setAttribute("aria-expanded", "false");

    function abrirMenu() {

        sidebar.classList.add("open");

        overlay.classList.add("active");

        document.body.classList.add("sidebar-open");

        botaoMenu.setAttribute("aria-expanded", "true");

    }

    function fecharMenu() {

        sidebar.classList.remove("open");

        overlay.classList.remove("active");

        document.body.classList.remove("sidebar-open");

        botaoMenu.setAttribute("aria-expanded", "false");

    }

    botaoMenu.addEventListener("click", () => {

        if (sidebar.classList.contains("open")) {

            fecharMenu();

        } else {

            abrirMenu();

        }

    });

    overlay.addEventListener("click", fecharMenu);

    document.addEventListener("keydown", (evento) => {

        if (
            evento.key === "Escape" &&
            sidebar.classList.contains("open")
        ) {

            fecharMenu();

            botaoMenu.focus();

        }

    });

    sidebar.querySelectorAll(".nav-link").forEach(link => {

        link.addEventListener("click", () => {

            if (window.innerWidth <= 1024) {

                fecharMenu();

            }

        });

    });

    window.addEventListener("resize", () => {

        if (window.innerWidth > 1024) {

            fecharMenu();

        }

    });

}


/* ==================================================
   05. DATA ATUAL
================================================== */

function atualizarData() {

    const elementoData = document.getElementById("data-atual");

    if (!elementoData) return;

    const agora = new Date();

    const dataFormatada = agora.toLocaleDateString("pt-BR", {

        day: "2-digit",
        month: "long",
        year: "numeric"

    });

    // Preserva o ícone caso esteja dentro do elemento.

    const icone = elementoData.querySelector(
        "svg, [data-lucide]"
    );

    if (icone) {

        elementoData.replaceChildren(
            icone,
            document.createTextNode(" " + dataFormatada)
        );

    } else {

        elementoData.textContent = dataFormatada;

    }

}


/* ==================================================
   06. ANO AUTOMÁTICO NO RODAPÉ
================================================== */

function atualizarAno() {

    const elementoAno = document.getElementById("ano-atual");

    if (elementoAno) {

        elementoAno.textContent = new Date().getFullYear();

    }

}


/* ==================================================
   07. ALERTAS E NOTIFICAÇÕES
================================================== */

function inicializarAlertas() {

    const alertas = document.querySelectorAll(".alert");

    alertas.forEach(alerta => {

        const botaoFechar = alerta.querySelector(".alert-close");

        if (botaoFechar) {

            botaoFechar.addEventListener("click", () => {

                removerAlerta(alerta);

            });

        }

        // Apenas mensagens de sucesso desaparecem
        // automaticamente. Erros e avisos permanecem.

        if (alerta.classList.contains("alert-success")) {

            setTimeout(() => {

                removerAlerta(alerta);

            }, 5000);

        }

    });

}


function removerAlerta(alerta) {

    if (!alerta.isConnected) return;

    alerta.classList.add("hiding");

    setTimeout(() => {

        alerta.remove();

    }, 250);

}


/* ==================================================
   08. MÁSCARA DE TELEFONE
================================================== */

function inicializarMascaras() {

    const camposTelefone = document.querySelectorAll(".phone-mask");

    camposTelefone.forEach(campo => {

        campo.setAttribute("inputmode", "tel");

        campo.addEventListener("input", () => {

            campo.value = formatarTelefone(campo.value);

        });

        if (campo.value) {

            campo.value = formatarTelefone(campo.value);

        }

    });

}


function formatarTelefone(valor) {

    const numeros = valor.replace(/\D/g, "").slice(0, 11);

    if (numeros.length === 0) {

        return "";

    }

    if (numeros.length <= 2) {

        return "(" + numeros;

    }

    const ddd = numeros.slice(0, 2);

    const telefone = numeros.slice(2);

    if (telefone.length <= 4) {

        return `(${ddd}) ${telefone}`;

    }

    if (telefone.length <= 8) {

        return `(${ddd}) ${telefone.slice(0, 4)}-${telefone.slice(4)}`;

    }

    return `(${ddd}) ${telefone.slice(0, 5)}-${telefone.slice(5)}`;

}


/* ==================================================
   09. CONFIRMAÇÃO DE EXCLUSÃO
================================================== */

function inicializarExclusoes() {

    const formularios = document.querySelectorAll(".delete-form");

    formularios.forEach(formulario => {

        // Remove a confirmação inline do HTML para
        // evitar que duas confirmações sejam exibidas.

        formulario.removeAttribute("onsubmit");

        formulario.addEventListener("submit", evento => {

            const nome = formulario.dataset.nome || "este registro";

            const tipo = formulario.dataset.tipo || "registro";

            let mensagem;

            if (tipo === "consulta") {

                mensagem =
                    `Deseja realmente excluir a consulta de ${nome}?\n\n` +
                    "Essa ação não poderá ser desfeita.";

            } else {

                mensagem =
                    `Deseja realmente excluir ${nome}?\n\n` +
                    "Essa ação não poderá ser desfeita.";

            }

            const confirmado = window.confirm(mensagem);

            if (!confirmado) {

                evento.preventDefault();

            }

        });

    });

}


/* ==================================================
   10. VALIDAÇÕES COMPLEMENTARES
================================================== */

function inicializarValidacoes() {

    validarDataNascimento();

    validarTelefones();

    validarDataConsulta();

    validarCamposTexto();

}


function obterDataLocal(data = new Date()) {

    const ano = data.getFullYear();

    const mes = String(
        data.getMonth() + 1
    ).padStart(2, "0");

    const dia = String(
        data.getDate()
    ).padStart(2, "0");

    return `${ano}-${mes}-${dia}`;

}


/* VALIDAÇÃO DA DATA DE NASCIMENTO */

function validarDataNascimento() {

    const campo = document.getElementById("data_nascimento");

    if (!campo) return;

    campo.max = obterDataLocal();

    function verificar() {

        campo.setCustomValidity("");

        if (campo.value && campo.value > obterDataLocal()) {

            campo.setCustomValidity(
                "A data de nascimento não pode ser futura."
            );

        }

    }

    campo.addEventListener("input", verificar);

    campo.addEventListener("change", verificar);

    verificar();

}


/* VALIDAÇÃO DE TELEFONES */

function validarTelefones() {

    const campos = document.querySelectorAll(".phone-mask");

    campos.forEach(campo => {

        function verificar() {

            const numeros = campo.value.replace(/\D/g, "");

            campo.setCustomValidity("");

            if (
                numeros.length > 0 &&
                numeros.length !== 10 &&
                numeros.length !== 11
            ) {

                campo.setCustomValidity(
                    "Informe um telefone válido com DDD."
                );

            }

        }

        campo.addEventListener("input", verificar);

        campo.addEventListener("change", verificar);

        verificar();

    });

}


/* VALIDAÇÃO DA DATA DE CONSULTA */

function validarDataConsulta() {

    const formulario = document.getElementById("form-consulta");

    if (!formulario) return;

    const campoData = formulario.querySelector("#data");

    const campoStatus = formulario.querySelector("#status");

    if (!campoData || !campoStatus) return;

    function verificar() {

        campoData.setCustomValidity("");

        const hoje = obterDataLocal();

        if (campoStatus.value === "Agendada") {

            campoData.min = hoje;

            if (campoData.value && campoData.value < hoje) {

                campoData.setCustomValidity(
                    "Uma consulta agendada não pode possuir data passada."
                );

            }

        } else {

            campoData.removeAttribute("min");

        }

    }

    campoData.addEventListener("input", verificar);

    campoData.addEventListener("change", verificar);

    campoStatus.addEventListener("change", verificar);

    verificar();

}


/* VALIDAÇÃO DE CAMPOS DE TEXTO */

function validarCamposTexto() {

    const campos = document.querySelectorAll(

        ".standard-form input[type='text'][required]"

    );

    campos.forEach(campo => {

        function verificar() {

            campo.setCustomValidity("");

            if (campo.value.length > 0 && !campo.value.trim()) {

                campo.setCustomValidity(
                    "Este campo não pode conter apenas espaços."
                );

            }

        }

        campo.addEventListener("input", verificar);

        campo.addEventListener("blur", () => {

            campo.value = campo.value.trim();

            verificar();

        });

        verificar();

    });

}


/* ==================================================
   11. RESUMO DINÂMICO DA CONSULTA
================================================== */

function inicializarResumoConsulta() {

    const formulario = document.getElementById("form-consulta");

    if (!formulario) return;

    const campoPaciente = formulario.querySelector("#paciente_id");

    const campoMedico = formulario.querySelector("#medico_id");

    const campoData = formulario.querySelector("#data");

    const campoHorario = formulario.querySelector("#horario");

    const campoStatus = formulario.querySelector("#status");

    function atualizarResumo() {

        /* PACIENTE */

        if (campoPaciente) {

            const opcaoPaciente =
                campoPaciente.options[campoPaciente.selectedIndex];

            atualizarTexto(

                "resumo-paciente",

                campoPaciente.value && opcaoPaciente
                    ? opcaoPaciente.textContent.trim()
                    : "Não selecionado"

            );

        }


        /* MÉDICO E ESPECIALIDADE */

        if (campoMedico) {

            const opcaoMedico =
                campoMedico.options[campoMedico.selectedIndex];

            if (campoMedico.value && opcaoMedico) {

                const especialidade =
                    opcaoMedico.dataset.especialidade || "";

                let nomeMedico = opcaoMedico.textContent
                    .replace(/\s+/g, " ")
                    .trim();

                const sufixo = " - " + especialidade;

                if (
                    especialidade &&
                    nomeMedico.endsWith(sufixo)
                ) {

                    nomeMedico = nomeMedico.slice(
                        0,
                        -sufixo.length
                    );

                }

                atualizarTexto(

                    "resumo-medico",
                    nomeMedico

                );

                atualizarTexto(

                    "resumo-especialidade",
                    especialidade || "Não informada"

                );

            } else {

                atualizarTexto(
                    "resumo-medico",
                    "Não selecionado"
                );

                atualizarTexto(
                    "resumo-especialidade",
                    "Não selecionada"
                );

            }

        }


        /* DATA */

        if (campoData) {

            atualizarTexto(

                "resumo-data",

                campoData.value
                    ? formatarData(campoData.value)
                    : "Não informada"

            );

        }


        /* HORÁRIO */

        if (campoHorario) {

            atualizarTexto(

                "resumo-horario",

                campoHorario.value || "Não informado"

            );

        }


        /* STATUS */

        if (campoStatus) {

            atualizarTexto(

                "resumo-status",

                campoStatus.value || "Agendada"

            );

        }

    }

    const campos = [

        campoPaciente,
        campoMedico,
        campoData,
        campoHorario,
        campoStatus

    ];

    campos.forEach(campo => {

        if (!campo) return;

        campo.addEventListener("input", atualizarResumo);

        campo.addEventListener("change", atualizarResumo);

    });

    atualizarResumo();

}


function atualizarTexto(id, valor) {

    const elemento = document.getElementById(id);

    if (elemento) {

        elemento.textContent = valor;

    }

}


function formatarData(data) {

    const partes = data.split("-");

    if (partes.length !== 3) return data;

    const [ano, mes, dia] = partes;

    return `${dia}/${mes}/${ano}`;

}


/* ==================================================
   12. PREVENÇÃO DE ENVIOS DUPLICADOS
================================================== */

function inicializarFormularios() {

    const formularios = document.querySelectorAll(

        ".standard-form, .delete-form, .status-form"

    );

    formularios.forEach(formulario => {

        formulario.addEventListener("submit", evento => {

            if (evento.defaultPrevented) return;

            if (formulario.dataset.enviando === "true") {

                evento.preventDefault();

                return;

            }

            if (!formulario.checkValidity()) {

                evento.preventDefault();

                formulario.reportValidity();

                return;

            }

            formulario.dataset.enviando = "true";

            const botao = formulario.querySelector(
                "button[type='submit']"
            );

            if (botao) {

                botao.disabled = true;

                botao.setAttribute("aria-busy", "true");

                if (
                    formulario.classList.contains("standard-form")
                ) {

                    botao.dataset.textoOriginal = botao.innerHTML;

                    botao.innerHTML = `
                        <i data-lucide="loader-circle"></i>
                        Salvando...
                    `;

                    const icone = botao.querySelector("i");

                    if (icone) {

                        icone.style.animation =
                            "medcontrol-spin 1s linear infinite";

                    }

                    atualizarIcones();

                }

            }

        });

    });

    // Restaura os botões ao voltar pelo histórico
    // do navegador.

    window.addEventListener("pageshow", evento => {

        if (!evento.persisted) return;

        formularios.forEach(formulario => {

            if (formulario.dataset.enviando !== "true") return;

            delete formulario.dataset.enviando;

            const botao = formulario.querySelector(
                "button[type='submit']"
            );

            if (!botao) return;

            botao.disabled = false;

            botao.removeAttribute("aria-busy");

            if (botao.dataset.textoOriginal) {

                botao.innerHTML = botao.dataset.textoOriginal;

                delete botao.dataset.textoOriginal;

            }

        });

        atualizarIcones();

    });

}


/* ==================================================
   13. ALTERAÇÃO DE STATUS
================================================== */

function inicializarStatus() {

    const seletores = document.querySelectorAll(".status-select");

    seletores.forEach(seletor => {

        const valorOriginal = seletor.value;

        const formulario = seletor.closest(".status-form");

        if (!formulario) return;

        const botao = formulario.querySelector(
            "button[type='submit']"
        );

        if (!botao) return;

        function atualizarBotao() {

            const alterado = seletor.value !== valorOriginal;

            botao.disabled = !alterado;

            botao.title = alterado
                ? "Salvar novo status"
                : "Selecione um status diferente";

        }

        seletor.addEventListener("change", atualizarBotao);

        atualizarBotao();

    });

}


/* ==================================================
   14. ANIMAÇÃO DE CARREGAMENTO
================================================== */

const estiloAnimacao = document.createElement("style");

estiloAnimacao.textContent = `

    @keyframes medcontrol-spin {

        from {
            transform: rotate(0deg);
        }

        to {
            transform: rotate(360deg);
        }

    }

    @media (prefers-reduced-motion: reduce) {

        [aria-busy="true"] svg {
            animation: none !important;
        }

    }

`;

document.head.appendChild(estiloAnimacao);


/* ==================================================
   FIM — MEDCONTROL
================================================== */
