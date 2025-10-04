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
        Renderiza um card de estufa

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

        # Container com borda colorida
        with st.container():
            # Header da estufa
            col_emoji, col_nome = st.columns([1, 11])
            with col_emoji:
                st.markdown(f"<h2>{emoji}</h2>", unsafe_allow_html=True)
            with col_nome:
                st.markdown(f"### {nome}")

            st.markdown(f"**📍 Cultura:** {cultura}")

            # Métricas em colunas
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="🌡️ Temperatura",
                    value=f"{temperatura:.1f}°C",
                    delta=None
                )

            with col2:
                st.metric(
                    label="💧 Umidade",
                    value=f"{umidade:.1f}%",
                    delta=None
                )

            # Status badge
            st.markdown(
                f'<div style="background-color: {color}; color: white; padding: 8px; '
                f'border-radius: 5px; text-align: center; font-weight: bold; margin-top: 10px;">'
                f'{status.upper()}'
                f'</div>',
                unsafe_allow_html=True
            )

            # Linha separadora com cor do status
            st.markdown(
                f'<div style="height: 3px; background-color: {color}; margin-top: 10px; border-radius: 2px;"></div>',
                unsafe_allow_html=True
            )
