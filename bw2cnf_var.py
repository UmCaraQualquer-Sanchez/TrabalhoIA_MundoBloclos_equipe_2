#!/usr/bin/env python3
"""
Gerador CNF para o T1 - Mundo dos Blocos de Tamanho Variável.

Uso:
    python3 bw2cnf_var.py 1
    python3 bw2cnf_var.py 2
    python3 bw2cnf_var.py 3

Com --resolver, tenta executar MiniSat 2.2 por meio do PySAT:
    python3 bw2cnf_var.py 1 --resolver

Os arquivos de cada cenário são gravados em:
    situacao1/
    situacao2/
    situacao3/
"""

import argparse
from itertools import combinations
from pathlib import Path

BLOCKS = {
    "a": 1,
    "b": 1,
    "c": 2,
    "d": 3,
}

MAX_POINT = 6
MAX_LEVEL = 3
TABLE = "T"

SCENARIOS = {
    1: {
        "initial": {
            "c": (0, 0),
            "a": (3, 0),
            "b": (5, 0),
            "d": (3, 1),
        },
        "goal": {
            "c": (0, 0),
            "a": (0, 1),
            "d": (2, 0),
            "b": (5, 0),
        },
        "horizon": 4,
    },
    2: {
        "initial": {
            "a": (0, 1),
            "b": (1, 1),
            "c": (0, 0),
            "d": (3, 0),
        },
        "goal": {
            "a": (4, 2),
            "b": (5, 2),
            "c": (4, 1),
            "d": (3, 0),
        },
        "horizon": 5,
    },
    3: {
        "initial": {
            "c": (0, 0),
            "a": (3, 0),
            "b": (5, 0),
            "d": (3, 1),
        },
        "goal": {
            "c": (0, 0),
            "a": (0, 1),
            "b": (1, 1),
            "d": (3, 0),
        },
        "horizon": 6,
    },
}


def valid_positions(block):
    """Posições iniciais possíveis para um bloco não ultrapassar a mesa."""
    length = BLOCKS[block]
    return range(MAX_POINT - length + 1)


def slots_of(block, position):
    """Slots ocupados pelo bloco quando começa em position."""
    length = BLOCKS[block]
    return set(range(position, position + length))


def spans_overlap(block1, p1, block2, p2):
    """Verdadeiro quando dois blocos compartilham pelo menos um slot."""
    return bool(slots_of(block1, p1) & slots_of(block2, p2))


class CNFBuilder:
    def __init__(self, horizon):
        self.horizon = horizon
        self.next_id = 1
        self.clauses = []
        self.names = {}

        self.at = {}
        self.lev = {}
        self.pos = {}
        self.occ = {}
        self.clr = {}
        self.mv = {}

        self._create_variables()

    def new_var(self, name):
        number = self.next_id
        self.next_id += 1
        self.names[number] = name
        return number

    def add(self, *literals):
        self.clauses.append(list(literals))

    def exactly_one(self, variables):
        """Pelo menos uma e no máximo uma."""
        self.add(*variables)

        for a, b in combinations(variables, 2):
            self.add(-a, -b)

    def _create_variables(self):
        # Estados existem de t=0 até t=H.
        for t in range(self.horizon + 1):
            for b in BLOCKS:
                for p in valid_positions(b):
                    self.at[(b, p, t)] = self.new_var(
                        f"at({b},{p},{t})"
                    )

                for level in range(MAX_LEVEL + 1):
                    self.lev[(b, level, t)] = self.new_var(
                        f"lev({b},{level},{t})"
                    )

                    for p in valid_positions(b):
                        self.pos[(b, p, level, t)] = self.new_var(
                            f"pos({b},{p},{level},{t})"
                        )

                for level in range(MAX_LEVEL + 1):
                    for slot in range(MAX_POINT):
                        self.occ[(slot, level, t)] = self.new_var(
                            f"occ({slot},{level},{t})"
                        )

                self.clr[(b, t)] = self.new_var(f"clr({b},{t})")

        # Uma ação acontece entre t e t+1.
        for t in range(self.horizon):
            for b in BLOCKS:
                for support in [TABLE] + [
                    x for x in BLOCKS if x != b
                ]:
                    for p in valid_positions(b):
                        self.mv[(b, support, p, t)] = self.new_var(
                            f"move({b},{support},{p},{t})"
                        )

    def encode(self, initial, goal):
        self._encode_state_structure()
        self._encode_pos_equivalence()
        self._encode_occupancy()
        self._encode_collision()
        self._encode_stability()
        self._encode_clear()
        self._encode_initial(initial)
        self._encode_goal(goal)
        self._encode_actions()
        self._encode_frames()
        self._encode_one_action_per_step()

    def _encode_state_structure(self):
        for t in range(self.horizon + 1):
            for b in BLOCKS:
                self.exactly_one(
                    [
                        self.at[(b, p, t)]
                        for p in valid_positions(b)
                    ]
                )

                self.exactly_one(
                    [
                        self.lev[(b, level, t)]
                        for level in range(MAX_LEVEL + 1)
                    ]
                )

    def _encode_pos_equivalence(self):
        """
        pos(b,p,l,t) <-> at(b,p,t) AND lev(b,l,t).
        """
        for t in range(self.horizon + 1):
            for b in BLOCKS:
                for p in valid_positions(b):
                    for level in range(MAX_LEVEL + 1):
                        pos = self.pos[(b, p, level, t)]
                        at = self.at[(b, p, t)]
                        lev = self.lev[(b, level, t)]

                        self.add(-pos, at)
                        self.add(-pos, lev)
                        self.add(-at, -lev, pos)

    def _encode_occupancy(self):
        """
        occ(slot,level,t) <-> existe algum bloco naquele slot e nível.
        """
        for t in range(self.horizon + 1):
            for level in range(MAX_LEVEL + 1):
                for slot in range(MAX_POINT):
                    occ = self.occ[(slot, level, t)]
                    covering = []

                    for b in BLOCKS:
                        for p in valid_positions(b):
                            if slot in slots_of(b, p):
                                covering.append(
                                    self.pos[(b, p, level, t)]
                                )
                                self.add(
                                    -self.pos[(b, p, level, t)],
                                    occ
                                )

                    # Se occ é verdadeira, algum bloco deve ocupá-la.
                    self.add(-occ, *covering)

    def _encode_collision(self):
        """
        Dois blocos diferentes não podem ocupar o mesmo slot no mesmo nível.
        """
        for t in range(self.horizon + 1):
            for level in range(MAX_LEVEL + 1):
                possibilities = []

                for b in BLOCKS:
                    for p in valid_positions(b):
                        possibilities.append(
                            (b, p, self.pos[(b, p, level, t)])
                        )

                for (b1, p1, v1), (b2, p2, v2) in combinations(
                    possibilities, 2
                ):
                    if b1 != b2 and spans_overlap(
                        b1, p1, b2, p2
                    ):
                        self.add(-v1, -v2)

    def _encode_stability(self):
        """
        Acima da mesa, o bloco precisa de ceil(tamanho/2) slots
        ocupados diretamente abaixo.
        """
        for t in range(self.horizon + 1):
            for b in BLOCKS:
                required = (BLOCKS[b] + 1) // 2

                for p in valid_positions(b):
                    support_slots = sorted(slots_of(b, p))

                    for level in range(1, MAX_LEVEL + 1):
                        pos = self.pos[(b, p, level, t)]

                        # Para garantir pelo menos k ocupados,
                        # toda combinação de n-k+1 slots precisa ter
                        # pelo menos um slot ocupado.
                        subset_size = len(support_slots) - required + 1

                        for subset in combinations(
                            support_slots, subset_size
                        ):
                            self.add(
                                -pos,
                                *[
                                    self.occ[(slot, level - 1, t)]
                                    for slot in subset
                                ],
                            )

    def _encode_clear(self):
        """
        clr(b,t) só pode ser verdadeiro quando não existe outro bloco
        em nível superior compartilhando algum slot.

        Também colocamos a direção inversa: se b está em uma posição/nível
        sem nenhum bloco acima, clr deve ser verdadeiro.
        """
        for t in range(self.horizon + 1):
            for b in BLOCKS:
                for p in valid_positions(b):
                    for level in range(MAX_LEVEL + 1):
                        base = self.pos[(b, p, level, t)]
                        blockers = []

                        for other in BLOCKS:
                            if other == b:
                                continue

                            for q in valid_positions(other):
                                if not spans_overlap(
                                    b, p, other, q
                                ):
                                    continue

                                for higher in range(
                                    level + 1, MAX_LEVEL + 1
                                ):
                                    blockers.append(
                                        self.pos[
                                            (other, q, higher, t)
                                        ]
                                    )
                                    self.add(
                                        -base,
                                        -self.pos[
                                            (other, q, higher, t)
                                        ],
                                        -self.clr[(b, t)],
                                    )

                        # Se base é verdadeira e nenhum blocker existe,
                        # clr deve ser verdadeira.
                        self.add(
                            -base,
                            *blockers,
                            self.clr[(b, t)],
                        )

    def _encode_initial(self, initial):
        for b, (p, level) in initial.items():
            self.add(self.at[(b, p, 0)])
            self.add(self.lev[(b, level, 0)])

    def _encode_goal(self, goal):
        final_t = self.horizon

        for b, (p, level) in goal.items():
            self.add(self.at[(b, p, final_t)])
            self.add(self.lev[(b, level, final_t)])

    def _encode_actions(self):
        for t in range(self.horizon):
            for b in BLOCKS:
                for support in [TABLE] + [
                    x for x in BLOCKS if x != b
                ]:
                    for p in valid_positions(b):
                        move = self.mv[(b, support, p, t)]

                        # O bloco movido precisa estar livre.
                        self.add(-move, self.clr[(b, t)])

                        if support == TABLE:
                            new_level = 0

                            # Não permitir movimento que não muda o estado.
                            self.add(
                                -move,
                                -self.pos[
                                    (b, p, new_level, t)
                                ],
                            )

                            # O destino na mesa precisa estar livre.
                            for other in BLOCKS:
                                if other == b:
                                    continue

                                for q in valid_positions(other):
                                    if spans_overlap(
                                        b, p, other, q
                                    ):
                                        self.add(
                                            -move,
                                            -self.pos[
                                                (other, q, 0, t)
                                            ],
                                        )

                            # Efeito.
                            self.add(
                                -move,
                                self.at[(b, p, t + 1)],
                            )
                            self.add(
                                -move,
                                self.lev[(b, 0, t + 1)],
                            )

                        else:
                            # O apoio precisa estar em uma posição que
                            # compartilhe pelo menos um slot com b.
                            support_positions = [
                                q
                                for q in valid_positions(support)
                                if spans_overlap(
                                    b, p, support, q
                                )
                            ]

                            self.add(
                                -move,
                                *[
                                    self.at[
                                        (support, q, t)
                                    ]
                                    for q in support_positions
                                ],
                            )

                            # Para cada nível possível do bloco de apoio,
                            # b ficará no nível imediatamente acima.
                            for support_level in range(
                                MAX_LEVEL
                            ):
                                new_level = support_level + 1

                                # Se support está nesse nível, o novo
                                # nível de b é determinado.
                                self.add(
                                    -move,
                                    -self.lev[
                                        (
                                            support,
                                            support_level,
                                            t,
                                        )
                                    ],
                                    self.lev[
                                        (
                                            b,
                                            new_level,
                                            t + 1,
                                        )
                                    ],
                                )

                                # O espaço acima do apoio precisa estar
                                # livre para a área ocupada por b.
                                for other in BLOCKS:
                                    if other in (b, support):
                                        continue

                                    for q in valid_positions(other):
                                        if spans_overlap(
                                            b, p, other, q
                                        ):
                                            self.add(
                                                -move,
                                                -self.lev[
                                                    (
                                                        support,
                                                        support_level,
                                                        t,
                                                    )
                                                ],
                                                -self.pos[
                                                    (
                                                        other,
                                                        q,
                                                        new_level,
                                                        t,
                                                    )
                                                ],
                                            )

                                # Não permitir no-op.
                                self.add(
                                    -move,
                                    -self.pos[
                                        (
                                            b,
                                            p,
                                            new_level,
                                            t,
                                        )
                                    ],
                                )

                            # Efeito da posição.
                            self.add(
                                -move,
                                self.at[(b, p, t + 1)],
                            )

    def _encode_frames(self):
        """
        Se um bloco não é o bloco movido no instante t, sua posição e
        nível permanecem iguais. Se ele é movido, as pré-condições/efeitos
        da ação determinam o novo estado.
        """
        for t in range(self.horizon):
            for b in BLOCKS:
                moves_of_b = [
                    self.mv[(b, support, p, t)]
                    for support in [TABLE] + [
                        x for x in BLOCKS if x != b
                    ]
                    for p in valid_positions(b)
                ]

                for p in valid_positions(b):
                    old = self.at[(b, p, t)]
                    new = self.at[(b, p, t + 1)]

                    # Se b não se move, a posição persiste.
                    self.add(*moves_of_b, -old, new)
                    self.add(*moves_of_b, -new, old)

                for level in range(MAX_LEVEL + 1):
                    old = self.lev[(b, level, t)]
                    new = self.lev[(b, level, t + 1)]

                    self.add(*moves_of_b, -old, new)
                    self.add(*moves_of_b, -new, old)

    def _encode_one_action_per_step(self):
        for t in range(self.horizon):
            actions = [
                self.mv[(b, support, p, t)]
                for b in BLOCKS
                for support in [TABLE] + [
                    x for x in BLOCKS if x != b
                ]
                for p in valid_positions(b)
            ]

            self.exactly_one(actions)

    def write_dimacs(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                f"p cnf {self.next_id - 1} "
                f"{len(self.clauses)}\n"
            )

            for clause in self.clauses:
                f.write(
                    " ".join(map(str, clause)) + " 0\n"
                )

    def write_map(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for number in sorted(self.names):
                f.write(
                    f"{number} {self.names[number]}\n"
                )


def solve_with_pysat(cnf_path, result_path):
    try:
        from pysat.solvers import Minisat22
    except ImportError:
        print(
            "PySAT não está instalado. "
            "Use: python3 -m pip install python-sat"
        )
        return False

    clauses = []

    with open(cnf_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("c"):
                continue

            if line.startswith("p"):
                continue

            values = [int(x) for x in line.split()]
            clauses.append(
                [x for x in values if x != 0]
            )

    with Minisat22(bootstrap_with=clauses) as solver:
        sat = solver.solve()

        with open(result_path, "w", encoding="utf-8") as f:
            if not sat:
                f.write("UNSAT\n")
                return True

            model = solver.get_model()
            f.write("SAT\n")
            f.write(
                " ".join(map(str, model)) + " 0\n"
            )

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario",
        type=int,
        choices=[1, 2, 3],
    )
    parser.add_argument(
        "--resolver",
        action="store_true",
        help="executa MiniSat 2.2 via PySAT",
    )
    args = parser.parse_args()

    scenario = SCENARIOS[args.scenario]

    output_dir = Path(
        f"situacao{args.scenario}"
    )
    output_dir.mkdir(exist_ok=True)

    builder = CNFBuilder(scenario["horizon"])
    builder.encode(
        scenario["initial"],
        scenario["goal"],
    )

    cnf_path = output_dir / "trab01_blocos2SAT.cnf"
    map_path = output_dir / "trab01_blocos2SAT.map"
    result_path = (
        output_dir / f"resultado{args.scenario}.txt"
    )

    builder.write_dimacs(cnf_path)
    builder.write_map(map_path)

    print(
        f"Situação {args.scenario}: "
        f"{builder.next_id - 1} variáveis, "
        f"{len(builder.clauses)} cláusulas."
    )
    print(f"CNF: {cnf_path}")
    print(f"MAP: {map_path}")

    if args.resolver:
        if solve_with_pysat(cnf_path, result_path):
            print(f"Resultado: {result_path}")


if __name__ == "__main__":
    main()
