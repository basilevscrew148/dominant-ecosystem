//! Демо и сценарии кросс-валидации (зеркала dominant_sim.py v1 и dominant_sim2.py v2).
//!
//! Запуск:
//!   cargo run --release --                    # демо (5 стимулов, таблица траектории)
//!   cargo run --release -- --scenario v1      # сценарий v1: инерция + сопряжённое торможение
//!   cargo run --release -- --scenario v2      # сценарий v2, без хронотопа
//!   cargo run --release -- --scenario v2 --chrono  # сценарий v2, с тягой хронотопа
//!
//! Машиночитаемый итог сценария — строка `FINAL x0 x1 ...`.

use dominant_rs::*;
use std::env;

const DEMO_STIMULI: [Stimulus; 5] = [
    Stimulus { id: "работа (доминанта-цель)", salience: 0.45, goal_relevance: 1.0 },
    Stimulus { id: "уведомления", salience: 0.55, goal_relevance: 0.0 },
    Stimulus { id: "письмо по теме", salience: 0.50, goal_relevance: 0.9 },
    Stimulus { id: "новости/шум", salience: 0.40, goal_relevance: 0.0 },
    Stimulus { id: "идея-инкубатор", salience: 0.35, goal_relevance: 0.6 },
];

fn demo() {
    let p = Params { dominance_threshold: 0.5, dominance_gap: 0.2, ..Default::default() };
    let goal = 2;
    let mut rng = Rng::new(7);
    let mut x: Vec<f64> = vec![0.0; DEMO_STIMULI.len()];
    let s: Vec<f64> = DEMO_STIMULI.iter().map(|st| st.salience).collect();
    let g: Vec<f64> = DEMO_STIMULI.iter().map(|st| st.goal_relevance).collect();

    println!("dominant-rs демо (цель: {})", DEMO_STIMULI[goal].id);
    let mut dominant_now: Option<usize> = None;
    let mut resolved_at: Option<usize> = None;
    let mut parking: Vec<&'static str> = Vec::new();
    for t in 0..40 {
        step(&mut x, &p, &mut rng, goal, &s, &g);
        let new_dominant = dominant(&x, &p);
        if new_dominant != dominant_now {
            dominant_now = new_dominant;
            match dominant_now {
                Some(d) => println!("t={t}: доминанта захвачена: {}", DEMO_STIMULI[d].id),
                None => println!("t={t}: доминанта потеряна (конкуренция)"),
            }
        }
        if resolved_at.is_none() && dominant_now == Some(goal) {
            resolved_at = Some(t);
        }
        if let Some(d) = dominant_now {
            for (i, st) in DEMO_STIMULI.iter().enumerate() {
                if i != d && !parking.contains(&st.id) {
                    parking.push(st.id);
                }
            }
        }
    }
    println!(
        "\nИтог: {}; парковка: {}",
        resolved_at
            .map(|t| format!("хронотоп разрешён на шаге {t}"))
            .unwrap_or_else(|| "цель не достигнута".into()),
        parking.join(", ")
    );
}

/// Сценарий v1 — зеркало dominant_sim.py: N=5, цель t∈[100,600) (s=1.5),
/// дистрактор t∈[350,380) (s=1.3). Параметры подобраны так, чтобы
/// ρ+w ≈ 1.2 (как self_w=1.2 в v1) — бистабильность → персистентность.
fn scenario_v1() {
    let p = Params {
        self_excitation: 0.4,
        inertia: 0.8,
        attention_gain: 0.3,
        noise: 0.02,
        ..Default::default()
    };
    let mut rng = Rng::new(7);
    let mut x: Vec<f64> = vec![0.0; 5];
    let g = [0.0f64; 5];
    for t in 0..1200 {
        let mut s = [0.0f64; 5];
        if (100..600).contains(&t) {
            s[0] = 1.5;
        }
        if (350..380).contains(&t) {
            s[1] = 1.3;
        }
        step(&mut x, &p, &mut rng, 0, &s, &g);
    }
    println!("FINAL {}", x.iter().map(|v| format!("{v:.3}")).collect::<Vec<_>>().join(" "));
}

/// Сценарий v2 — зеркало dominant_sim2.py: N=3, цель t∈[100,400) (s=1.5),
/// дистрактор t∈[300,330) (s=1.3). --chrono включает тягу хронотопа γ·(T−x).
fn scenario_v2(chrono: bool) {
    let p = Params {
        self_excitation: 0.1,
        inertia: 0.8,
        attention_gain: 0.3,
        noise: 0.02,
        chronotope_pull: if chrono { 0.05 } else { 0.0 },
        ..Default::default()
    };
    let mut rng = Rng::new(7);
    let mut x: Vec<f64> = vec![0.0; 3];
    let g = [if chrono { 1.0 } else { 0.0 }, 0.0, 0.0];
    for t in 0..600 {
        let mut s = [0.0f64; 3];
        if (100..400).contains(&t) {
            s[0] = 1.5;
        }
        if (300..330).contains(&t) {
            s[1] = 1.3;
        }
        step(&mut x, &p, &mut rng, 0, &s, &g);
        if t == 335 {
            println!("MID {}", x.iter().map(|v| format!("{v:.3}")).collect::<Vec<_>>().join(" "));
        }
    }
    println!("FINAL {}", x.iter().map(|v| format!("{v:.3}")).collect::<Vec<_>>().join(" "));
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        None => demo(),
        Some("--scenario") => match args.get(2).map(|s| s.as_str()) {
            Some("v1") => scenario_v1(),
            Some("v2") => scenario_v2(args.iter().any(|a| a == "--chrono")),
            other => panic!("неизвестный сценарий: {other:?}"),
        },
        other => panic!("неизвестный аргумент: {other:?}"),
    }
}
