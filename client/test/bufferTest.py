import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from buffer import BufferManager

def test_buffer_manager():
    print("=== Iniciando Testes do BufferManager ===\n")
    
    # Instancia o gerenciador do buffer
    bm = BufferManager()
    
    # -------------------------------------------------------------
    # Teste 1: Estado Inicial e Abastecimento
    # -------------------------------------------------------------
    print("Teste 1: Estado inicial e adição de segmentos...")
    assert bm.buffer_level_s == 0.0, "Erro: O buffer deveria começar em 0"
    assert bm.can_play() is False, "Erro: Não deveria poder jogar com buffer zerado"
    
    # Baixou o primeiro segmento (vamos supor que o SEGMENT_DURATION padrão seja 4.0 segundos)
    bm.add_segment(4.0)
    print(f" - Adicionado segmento de 4s. Buffer atual: {bm.buffer_level_s}s")
    assert bm.buffer_level_s == 4.0, "Erro: Buffer deveria ser 4.0"
    
    # Baixou o segundo segmento
    bm.add_segment(4.0)
    print(f" - Adicionado mais um segmento de 4s. Buffer atual: {bm.buffer_level_s}s")
    assert bm.buffer_level_s == 8.0, "Erro: Buffer deveria ser 8.0"
    print("✓ Teste 1 passou!\n")

    # -------------------------------------------------------------
    # Teste 2: Cenário 1 - O buffer aguenta o tranco (Sem travamentos)
    # -------------------------------------------------------------
    print("Teste 2: Cenário 1 - Consumo menor que o buffer disponível...")
    # O player tem 8s de vídeo guardado e se passam 3s de reprodução/download
    bm.consume(3.0)
    
    had_stall, stall_time = bm.check_rebuffer()
    print(f" - Buffer após consumir 3s: {bm.buffer_level_s}s")
    print(f" - Houve travamento? {had_stall} | Tempo de travamento: {stall_time}s")
    
    assert bm.buffer_level_s == 5.0, "Erro: O buffer deveria ter caído para 5.0"
    assert had_stall is False, "Erro: Não deveria ter travado"
    assert stall_time == 0.0, "Erro: O tempo de travamento deveria ser 0"
    print("✓ Teste 2 (Cenário 1) passou!\n")

    # -------------------------------------------------------------
    # Teste 3: Cenário 2 - O buffer zera e trava parcialmente
    # -------------------------------------------------------------
    print("Teste 3: Cenário 2 - Tempo decorrido maior que o buffer (Travamento parcial)...")
    # O player tem 5s de buffer, mas a rede engasga e se passam 7s
    bm.consume(7.0)
    
    had_stall, stall_time = bm.check_rebuffer()
    print(f" - Buffer após tentar consumir 7s: {bm.buffer_level_s}s")
    print(f" - Houve travamento? {had_stall} | Tempo de travamento: {stall_time}s")
    
    assert bm.buffer_level_s == 0.0, "Erro: O buffer deveria ter zerado"
    assert had_stall is True, "Erro: Deveria constar que travou"
    assert stall_time == 2.0, "Erro: O travamento deveria ter sido de exatamente 2.0s (7s - 5s)"
    print("✓ Teste 3 (Cenário 2) passou!\n")

    # -------------------------------------------------------------
    # Teste 4: Cenário 3 - O buffer já estava zerado (Travamento contínuo)
    # -------------------------------------------------------------
    print("Teste 4: Cenário 3 - Consumo com buffer já zerado (Travamento total)...")
    # O buffer está em 0 e se passam mais 4s esperando o download terminar
    bm.consume(4.0)
    
    had_stall, stall_time = bm.check_rebuffer()
    print(f" - Buffer continua em: {bm.buffer_level_s}s")
    print(f" - Houve travamento? {had_stall} | Tempo de travamento: {stall_time}s")
    
    assert bm.buffer_level_s == 0.0, "Erro: O buffer deve continuar zerado"
    assert had_stall is True, "Erro: Deve constar que travou"
    assert stall_time == 4.0, "Erro: Todo o tempo decorrido (4s) deveria ser de travamento"
    print("✓ Teste 4 (Cenário 3) passou!\n")

    # -------------------------------------------------------------
    # Teste 5: Validação da trava de reprodução (can_play)
    # -------------------------------------------------------------
    print("Teste 5: Verificando regra do can_play()...")
    # Vamos assumir que MIN_BUFFER_TO_PLAY na sua config seja 4.0 segundos
    bm.add_segment(2.0)
    print(f" - Adicionado 2s de vídeo. Buffer: {bm.buffer_level_s}s. Pode dar play? {bm.can_play(min_buffer=4.0)}")
    assert bm.can_play(min_buffer=4.0) is False, "Erro: Não deveria poder jogar com só 2s se o mínimo é 4s"
    
    bm.add_segment(2.0)
    print(f" - Adicionado mais 2s de vídeo. Buffer: {bm.buffer_level_s}s. Pode dar play? {bm.can_play(min_buffer=4.0)}")
    assert bm.can_play(min_buffer=4.0) is True, "Erro: Agora que chegou em 4s, deveria permitir o play"
    print("✓ Teste 5 passou!\n")

    print("=== TUDO CERTINHO! Todos os cenários do BufferManager funcionam perfeitamente. ===")

if __name__ == "__main__":
    test_buffer_manager()