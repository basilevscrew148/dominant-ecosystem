//! dominant-rs — исполняемая формальная модель доминанты А. А. Ухтомского.
//!
//! Модель объединяет три гипотезы экосистемы «Доминанта»:
//!   1) доминанта ≈ precision-weighting (Фристон): внимание повышает точность
//!      (precision) канала, соответствующего доминирующему очагу возбуждения;
//!   2) инерция: возбуждение накапливается и не исчезает мгновенно;
//!   3) хронотоп: цель (модель потребного будущего, Н. А. Бернштейн) смещает
//!      приоритеты стимулов, реализуя антиципацию разрешения.
//!
//! Запуск: cargo run -- [--steps N] [--seed S] [--goal G]
//! Пример: cargo run -- --steps 60 --seed 7 --goal 2

use std::env;

/// Стимул внешнего мира: сродство к цели (хронотоп) и «сырая» сила.
#[derive(Clone, Debug)]
struct Stimulus {
    id: &'static str,
    /// Базовая сила стимула (salience), 0..1.
    salience: f64,
    /// Сродство стимула цели (goal relevance), 0..1. Реализует хронотоп.
    goal_relevance: f64,
}

/// Состояние одного очага возбуждения.
#[derive(Clone, Copy, Debug)]
struct Focus {
    /// Уровень возбуждения (логит-подобная шкала).
    excitation: f64,
}

/// Параметры модели.
struct Params {
    /// Базовая точность (precision) канала без внимания.
    base_precision: f64,
    /// Прирост precision за единицу возбуждения (precision-weighting).
    attention_gain: f64,
    /// Инерция: доля возбуждения, сохраняющаяся за шаг (0..1).
    inertia: f64,
    /// Сопряжённое торможение: сила подавления конкурентов доминантой.
    lateral_inhibition: f64,
    /// Порог доминирования (очаг выше порога — кандидат в доминанты).
    dominance_threshold: f64,
    /// Минимальный разрыв между лидером и вторым (устойчивость доминанты).
    dominance_gap: f64,
    /// Шум среды (дисперсия гауссова шума на шаг).
    noise: f64,
}

/// Быстрый детерминированный ГПСЧ (xorshift64*), чтобы не тянуть зависимости.
struct Rng(u64);

impl Rng {
    fn new(seed: u64) -> Self {
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
    fn normal(&mut self) -> f64 {
        let u1 = (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
        let u2 = (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
        (-2.0 * u1.max(1e-12).ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }
}

/// Один шаг динамики: возбуждение, торможение, инерция, шум.
fn step(
    stimuli: &[Stimulus],
    foci: &mut [Focus],
    p: &Params,
    rng: &mut Rng,
    goal: usize,
) {
    let n = stimuli.len();
    // 1) Precision-weighting: внимание поднимает точность канала.
    let precisions: Vec<f64> = foci
        .iter()
        .map(|f| p.base_precision + p.attention_gain * f.excitation.max(0.0))
        .collect();
    // 2) Эффективный вход: salience * precision * (1 + хронотоп-усиление).
    let inputs: Vec<f64> = stimuli
        .iter()
        .enumerate()
        .map(|(i, s)| {
            let chronotope_boost = if i == goal { 1.0 } else { 0.0 };
            s.salience * precisions[i] * (1.0 + s.goal_relevance * chronotope_boost)
                + p.noise * rng.normal()
        })
        .collect();
    // 3) Сопряжённое торможение: лидер подавляет конкурентов.
    let leader = foci
        .iter()
        .enumerate()
        .max_by(|a, b| a.1.excitation.partial_cmp(&b.1.excitation).unwrap())
        .map(|(i, _)| i)
        .unwrap_or(0);
    let next: Vec<f64> = foci
        .iter()
        .enumerate()
        .map(|(i, f)| {
            let inhibition = if i != leader {
                p.lateral_inhibition * foci[leader].excitation.max(0.0)
            } else {
                0.0
            };
            // 4) Инерция + новый вход − торможение.
            p.inertia * f.excitation + inputs[i] - inhibition
        })
        .collect();
    for (i, f) in foci.iter_mut().enumerate() {
        f.excitation = next[i];
    }
}

fn main() {
    let mut steps = 60usize;
    let mut seed = 7u64;
    let mut goal = 2usize;

    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--steps" => {
                steps = args[i + 1].parse().expect("--steps N");
                i += 1;
            }
            "--seed" => {
                seed = args[i + 1].parse().expect("--seed S");
                i += 1;
            }
            "--goal" => {
                goal = args[i + 1].parse().expect("--goal G");
                i += 1;
            }
            other => panic!("неизвестный аргумент: {other}"),
        }
        i += 1;
    }

    let stimuli = vec![
        Stimulus { id: "работа (доминанта-цель)", salience: 0.45, goal_relevance: 1.0 },
        Stimulus { id: "уведомления", salience: 0.55, goal_relevance: 0.0 },
        Stimulus { id: "письмо по теме", salience: 0.50, goal_relevance: 0.9 },
        Stimulus { id: "новости/шум", salience: 0.40, goal_relevance: 0.0 },
        Stimulus { id: "идея-инкубатор", salience: 0.35, goal_relevance: 0.6 },
    ];
    assert!(goal < stimuli.len());

    let p = Params {
        base_precision: 1.0,
        attention_gain: 0.9,
        inertia: 0.85,
        lateral_inhibition: 0.35,
        dominance_threshold: 1.2,
        dominance_gap: 0.3,
        noise: 0.05,
    };

    let mut rng = Rng::new(seed);
    let mut foci: Vec<Focus> = vec![Focus { excitation: 0.0 }; stimuli.len()];
    let mut dominant: Option<usize> = None;
    let mut resolved_at: Option<usize> = None;
    let mut parking: Vec<&'static str> = Vec::new();

    println!("dominant-rs: {steps} шагов, seed={seed}, цель={}", stimuli[goal].id);
    println!("шаг\t{}\tдоминанта\tсобытие", stimuli.iter().map(|s| s.id).collect::<Vec<_>>().join("\t"));

    for t in 0..steps {
        step(&stimuli, &mut foci, &p, &mut rng, goal);

        // Определение доминанты: максимум выше порога и отрыв от второго.
        let mut order: Vec<usize> = (0..foci.len()).collect();
        order.sort_by(|&a, &b| foci[b].excitation.partial_cmp(&foci[a].excitation).unwrap());
        let leader = order[0];
        let runner_up = order[1];
        let leader_val = foci[leader].excitation;
        let gap = leader_val - foci[runner_up].excitation;

        let mut event = String::new();
        let new_dominant = if leader_val >= p.dominance_threshold && gap >= p.dominance_gap {
            Some(leader)
        } else {
            None
        };
        if new_dominant != dominant {
            dominant = new_dominant;
            event.push_str(if let Some(d) = dominant {
                &format!("доминанта захвачена: {}", stimuli[d].id)
            } else {
                "доминанта потеряна (конкуренция)"
            });
        }

        // Разрешение: доминанта совпала с целью — хронотоп замкнулся.
        if resolved_at.is_none() && dominant == Some(goal) {
            resolved_at = Some(t);
            event.push_str(" => ХРОНОТОП РАЗРЕШЁН: цель достигнута");
        }

        // Парковка: всё, что было подавлено, пока доминанта активна.
        if let Some(d) = dominant {
            for (i, s) in stimuli.iter().enumerate() {
                if i != d && !parking.contains(&s.id) {
                    parking.push(s.id);
                }
            }
        }

        let row: Vec<String> = foci.iter().map(|f| format!("{:.2}", f.excitation)).collect();
        println!("{t}\t{}\t{}\t{}", row.join("\t"), dominant.map(|d| stimuli[d].id).unwrap_or("—"), event);
    }

    match resolved_at {
        Some(t) => println!("\nИтог: цель достигнута на шаге {t} (антиципация разрешения сработала)."),
        None => println!("\nИтог: цель не достигнута за {steps} шагов (шум/торможение победили инерцию)."),
    }
    println!("Парковка (сопряжённо заторможенное): {}", parking.join(", "));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn доминанта_захватывается_целевым_стимулом() {
        let stimuli = vec![
            Stimulus { id: "цель", salience: 0.5, goal_relevance: 1.0 },
            Stimulus { id: "шум", salience: 0.6, goal_relevance: 0.0 },
        ];
        let p = Params {
            base_precision: 1.0,
            attention_gain: 0.9,
            inertia: 0.85,
            lateral_inhibition: 0.35,
            dominance_threshold: 1.2,
            dominance_gap: 0.3,
            noise: 0.0,
        };
        let mut rng = Rng::new(1);
        let mut foci = vec![Focus { excitation: 0.0 }; 2];
        for _ in 0..40 {
            step(&stimuli, &mut foci, &p, &mut rng, 0);
        }
        // Без шума хронотоп-усиление + инерция должны вывести цель в лидеры.
        assert!(foci[0].excitation > foci[1].excitation);
    }

    #[test]
    fn инерция_сохраняет_возбуждение_без_входа() {
        let p = Params {
            base_precision: 1.0,
            attention_gain: 0.9,
            inertia: 0.8,
            lateral_inhibition: 0.0,
            dominance_threshold: 9.9,
            dominance_gap: 0.0,
            noise: 0.0,
        };
        let mut rng = Rng::new(2);
        let stimuli = vec![Stimulus { id: "нет входа", salience: 0.0, goal_relevance: 0.0 }];
        let mut foci = vec![Focus { excitation: 1.0 }];
        step(&stimuli, &mut foci, &p, &mut rng, 0);
        // 0.8 * 1.0 = 0.8: возбуждение не обнуляется мгновенно.
        assert!((foci[0].excitation - 0.8).abs() < 1e-12);
    }
}
