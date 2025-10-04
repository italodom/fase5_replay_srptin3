"""
Componente de Card para exibir informações de uma estufa
"""
import streamlit as st
from typing import Dict


class EstufaCard:
    """Componente visual para exibir dados de uma estufa"""

    # Cores por status
    COLORS = {
        'Normal': '#28a745',    # Verde
        'Alerta': '#ffc107',    # Amarelo
        'Critico': '#dc3545'    # Vermelho
    }

    # Emojis por status
    EMOJIS = {
        'Normal': '✅',
        'Alerta': '⚠️',
        'Critico': '🚨'
    }

    @classmethod
    def render(cls, estufa_data: Dict):
        """
        Renderiza um card de estufa usando apenas componentes nativos

        Args:
            estufa_data: Dicionário com dados da estufa
        """
        nome = estufa_data.get('nome', 'Estufa')
        cultura = estufa_data.get('cultura', 'N/A')
        temperatura = estufa_data.get('temperatura', 0.0)
        umidade = estufa_data.get('umidade', 0.0)
        status = estufa_data.get('status', 'Normal')

        # Cor baseada no status
        color = cls.COLORS.get(status, '#6c757d')
        emoji = cls.EMOJIS.get(status, '❓')

        # Container principal com estilo dark
        container = st.container(border=True)

        with container:
            # Header com emoji e nome
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 24px; margin-right: 10px;">{emoji}</span>
                    <h2 style="margin: 0; color: #c9d1d9;">{nome}</h2>
                </div>
            """, unsafe_allow_html=True)

            # Cultura
            st.markdown(f"<p style='color: #8b949e; font-size: 0.9em;'>📍 <strong>{cultura}</strong></p>", unsafe_allow_html=True)

            st.markdown("<hr style='border-color: #30363d; margin: 12px 0;'>", unsafe_allow_html=True)

            # Métricas em colunas
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="🌡️ Temperatura",
                    value=f"{temperatura:.1f}°C"
                )

            with col2:
                st.metric(
                    label="💧 Umidade",
                    value=f"{umidade:.1f}%"
                )

            st.markdown("<hr style='border-color: #30363d; margin: 12px 0;'>", unsafe_allow_html=True)

            # Status badge usando markdown
            st.markdown(
                f"""<div style="background-color: {color}; color: white; padding: 12px;
                border-radius: 6px; text-align: center; font-weight: bold; font-size: 0.9em; letter-spacing: 0.5px;
                margin-bottom: 12px;">
                {status.upper()}
                </div>""",
                unsafe_allow_html=True
            )
