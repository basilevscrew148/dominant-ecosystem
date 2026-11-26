//! dominant-rs — исполняемая формальная модель доминанты А. А. Ухтомского.
//!
//! Модель (статья 07 экосистемы «Доминанта»):
//!   x_i(t+1) = tanh( ρ·x_i + w·max(x_i,0) + π_i·s_i·(1 + g_i·𝟙[i=goal]) + γ·g_i·(T − x_i)·𝟙[i=goal]
//!                    − κ·max(x_L,0)·𝟙[i≠L] + ε_i )
//!   π_i = π₀ + α·max(x_i,0)          — precision-weighting (гипотеза Радченко);
//!   ρ   — инерция; w — само-возбуждение (повышенная возбудимость, Шульгина);
//!   κ   — сопряжённое торможение от лидера L; γ·(T−x) — тяга хронотопа к цели;
//!   tanh — насыщение (предел частоты разряда; без него модель расходится).

pub struct Stimulus {
    pub id: &'static str,
    /// «Сырая» сила стимула (salience), 0..1 (для сценариев v1/v2 бывает >1).
    pub salience: f64,
    /// Сродство стимула цели (хронотоп-проекция), 0..1.
    pub goal_relevance: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Params {
    /// Базовая точность канала без внимания.
    pub base_precision: f64,
    /// Прирост precision за единицу возбуждения (precision-weighting).
    pub attention_gain: f64,
    /// Само-возбуждение (повышенная возбудимость очага).
    pub self_excitation: f64,
    /// Инерция: доля возбуждения, сохраняемая за шаг.
    pub inertia: f64,
    /// Сопряжённое торможение от лидера.
    pub lateral_inhibition: f64,
    /// Порог доминирования.
    pub dominance_threshold: f64,
    /// Минимальный отрыв лидера от второго.
    pub dominance_gap: f64,
    /// Дисперсия шума среды на шаг.
    pub noise: f64,
    /// Тяга хронотопа к цели (γ в уравнении).
    pub chronotope_pull: f64,
    /// Целевой уровень хронотопа (T).
    pub chronotope_target: f64,
}

impl Default for Params {
    fn default() -> Self {
        Params {
            base_precision: 1.0,
            attention_gain: 0.5,
            self_excitation: 0.2,
            inertia: 0.8,
            lateral_inhibition: 0.35,
            dominance_threshold: 0.5,
            dominance_gap: 0.2,
            noise: 0.02,
            chronotope_pull: 0.0,
            chronotope_target: 0.9,
        }
    }
}

/// xorshift64* — детерминированный ГПСЧ без внешних зависимостей.
pub struct Rng(u64);

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng(seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1).max(1))
    }
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    /// Стандартное нормальное число (Box–Muller).
    pub fn normal(&mut self) -> f64 {
        let u1 = (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
        let u2 = (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
        (-2.0 * u1.max(1e-12).ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }
}

/// Индекс лидера (максимум возбуждения).
pub fn leader_idx(foci: &[f64]) -> usize {
    foci.iter()
        .enumerate()
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
        .map(|(i, _)| i)
        .unwrap_or(0)
}

/// Доминанта: лидер выше порога и отрыв не меньше gap.
pub fn dominant(foci: &[f64], p: &Params) -> Option<usize> {
    if foci.len() < 2 {
        return (foci[0] >= p.dominance_threshold).then_some(0);
    }
    let mut order: Vec<usize> = (0..foci.len()).collect();
    order.sort_by(|&a, &b| foci[b].partial_cmp(&foci[a]).unwrap());
    let (l, r) = (order[0], order[1]);
    if foci[l] >= p.dominance_threshold && foci[l] - foci[r] >= p.dominance_gap {
        Some(l)
    } else {
        None
    }
}

/// Один шаг динамики. `salience`/`goal_relevance` — входы на этом шаге
/// (позволяет сценариям включать/выключать стимулы во времени).
pub fn step(
    foci: &mut [f64],
    p: &Params,
    rng: &mut Rng,
    goal: usize,
    salience: &[f64],
    goal_relevance: &[f64],
) {
    let leader = leader_idx(foci);
    let precisions: Vec<f64> = foci
        .iter()
        .map(|x| p.base_precision + p.attention_gain * x.max(0.0))
        .collect();
    let next: Vec<f64> = (0..foci.len())
        .map(|i| {
            let boost = if i == goal { 1.0 + goal_relevance[i] } else { 1.0 };
            let pull = if i == goal {
                p.chronotope_pull * goal_relevance[i] * (p.chronotope_target - foci[i])
            } else {
                0.0
            };
            let inhibition = if i != leader {
                p.lateral_inhibition * foci[leader].max(0.0)
            } else {
                0.0
            };
            let input = precisions[i] * salience[i] * boost + pull + p.noise * rng.normal();
            (p.inertia * foci[i] + p.self_excitation * foci[i].max(0.0) + input - inhibition).tanh()
        })
        .collect();
    foci.copy_from_slice(&next);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn доминанта_захватывается_целевым_стимулом() {
        let p = Params { noise: 0.0, ..Default::default() };
        let mut rng = Rng::new(1);
        let mut x = vec![0.0; 2];
        let s = [0.5, 0.6];
        let g = [1.0, 0.0];
        for _ in 0..60 {
            step(&mut x, &p, &mut rng, 0, &s, &g);
        }
        assert!(x[0] > x[1], "цель должна победить: {:?}", x);
    }

    #[test]
    fn инерция_сохраняет_возбуждение_без_входа() {
        let p = Params {
            self_excitation: 0.0,
            inertia: 0.8,
            noise: 0.0,
            ..Default::default()
        };
        let mut rng = Rng::new(2);
        let mut x = vec![1.0];
        step(&mut x, &p, &mut rng, 0, &[0.0], &[0.0]);
        assert!((x[0] - 0.8_f64.tanh()).abs() < 1e-12);
    }

    #[test]
    fn само_возбуждение_даёт_персистентность_после_снятия_стимула() {
        // ρ + w > 1 ⇒ ненулевая неподвижная точка: очаг не угасает без входа.
        let p = Params {
            self_excitation: 0.3,
            inertia: 0.8,
            noise: 0.0,
            ..Default::default()
        };
        let mut rng = Rng::new(3);
        let mut x = vec![0.5];
        for _ in 0..200 {
            step(&mut x, &p, &mut rng, 0, &[0.0], &[0.0]);
        }
        assert!(x[0] > 0.1, "персистентность не удержалась: x={}", x[0]);
    }

    #[test]
    fn хронотоп_тянет_очаг_к_цели_без_стимула() {
        let p = Params {
            noise: 0.0,
            chronotope_pull: 0.05,
            ..Default::default()
        };
        let mut rng = Rng::new(4);
        let mut x = vec![0.0];
        let g = [1.0];
        for _ in 0..300 {
            step(&mut x, &p, &mut rng, 0, &[0.0], &g);
        }
        assert!(x[0] > 0.1, "хронотоп не поднял очаг: x={}", x[0]);
    }
}
