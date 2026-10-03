# Mundo dos Blocos de Tamanho Variável

Trabalho T1 de Fundamentos de Inteligência Artificial.

O projeto trata de um Mundo dos Blocos com blocos de tamanhos diferentes. A descrição do problema foi feita em Lógica de Primeira Ordem e depois transformada em CNF para ser resolvida por um SAT Solver.

## Blocos

- `a` = tamanho 1
- `b` = tamanho 1
- `c` = tamanho 2
- `d` = tamanho 3

## Arquivos

```text
bw2cnf_var.py
requirements.txt
README.md

situacao1/
    trab01_blocos2SAT.cnf
    trab01_blocos2SAT.map
    resultado1.txt

situacao2/
    trab01_blocos2SAT.cnf
    trab01_blocos2SAT.map
    resultado2.txt

situacao3/
    trab01_blocos2SAT.cnf
    trab01_blocos2SAT.map
    resultado3.txt

latex/
    trabalho_FIA2.tex
```

O arquivo `bw2cnf_var.py` é o programa principal. Os arquivos `.cnf` e `.map` são gerados pelo programa e os arquivos `resultado1.txt`, `resultado2.txt` e `resultado3.txt` guardam os resultados do solver.

## Instalação

É necessário ter Python instalado.

Para instalar o PySAT:

```bash
python -m pip install -r requirements.txt
```

## Execução

Situação 1:

```bash
python bw2cnf_var.py 1 --resolver
```

Situação 2:

```bash
python bw2cnf_var.py 2 --resolver
```

Situação 3:

```bash
python bw2cnf_var.py 3 --resolver
```

## Resultados

### Situação 1

1441 variáveis e 28873 cláusulas.

Resultado: `SAT`

```text
1. move(d,c,0)
2. move(a,b,5)
3. move(d,T,2)
4. move(a,c,0)
```

Foi igual à resolução manual.

### Situação 2

1746 variáveis e 35666 cláusulas.

Resultado: `SAT`

```text
1. move(b,d,3)
2. move(a,T,2)
3. move(c,d,4)
4. move(b,c,5)
5. move(a,c,4)
```

O solver encontrou uma sequência diferente da resolução manual, mas que satisfaz o cenário.

### Situação 3

2051 variáveis e 42459 cláusulas.

Resultado: `SAT`

```text
1. move(d,c,0)
2. move(a,b,5)
3. move(d,T,2)
4. move(a,c,0)
5. move(b,c,1)
6. move(d,T,3)
```

Foi igual à resolução manual.

## Observação

Os três cenários foram executados e apresentaram resultado `SAT`.
