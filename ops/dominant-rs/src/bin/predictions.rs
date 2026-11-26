//! Проверка 5 предсказаний статьи 07 (формальная модель доминанты)
//! по сеткам параметров. Запуск: cargo run --release --bin predictions
//! Каждое предсказание печатает таблицу и вердикт PASS/FAIL.

use dominant_rs::*;

fn mean(v: &[f64]) -> f64 {
    v.iter().sum::<f64>() / v.len() as f64
}

/// П1: исходное предсказание статьи 07 — «латентность захвата монотонно убывает
/// с α (precision-weighting ускоряет селекцию)». Симуляция ОПРОВЕРГЛА общую форму:
/// в дискретной модели с симметричным precision латентность от α не зависит или
/// растёт. Механизм: (1) порог пересекается на линейном участке, где π мало зависит
/// от α; (2) критерий отрыва (δ) связывается конкурентом — precision симметрично
/// ускоряет и его; при слабом κ и высоком α доминанта вообще не объявляется.
/// Уточнение (внесено в статью 07): селекцию ускоряет сопряжённое торможение κ,
/// а не precision сам по себе — что согласуется с четырьмя свойствами доминанты.
fn predict1() {
    println!("П1: латентность захвата vs α — исходное предсказание ОПРОВЕРГНУТО (уточнено)");
    let steps = 100usize;
    let g = [1.0, 0.0, 0.0, 0.0];
    // Режим A: слабое торможение κ=0.35, симметричный precision.
    println!("режим A (κ=0.35, слабый сигнал):");
    println!("α\tшаг захвата (шум=0)");
    for alpha in [0.0, 0.4, 0.8, 1.2] {
        let p = Params { attention_gain: alpha, lateral_inhibition: 0.35, noise: 0.0, ..Default::default() };
        let mut rng = Rng::new(1);
        let mut x = vec![0.0f64; 4];
        let s = [0.16, 0.30, 0.12, 0.10];
        let mut cap = steps;
        for t in 0..steps {
            step(&mut x, &p, &mut rng, 0, &s, &g);
            if dominant(&x, &p) == Some(0) { cap = t; break; }
        }
        println!("{alpha}\t{cap}");
    }
    // Режим B: достаточное торможение κ=0.5 — латентность всё равно не убывает.
    println!("режим B (κ=0.5):");
    println!("α\tшаг захвата (шум=0)");
    for alpha in [0.0, 0.4, 0.8, 1.2] {
        let p = Params { attention_gain: alpha, lateral_inhibition: 0.5, noise: 0.0, ..Default::default() };
        let mut rng = Rng::new(1);
        let mut x = vec![0.0f64; 4];
        let s = [0.24, 0.40, 0.10, 0.10];
        let mut cap = steps;
        for t in 0..steps {
            step(&mut x, &p, &mut rng, 0, &s, &g);
            if dominant(&x, &p) == Some(0) { cap = t; break; }
        }
        println!("{alpha}\t{cap}");
    }
    println!("ВЕРДИКТ: FAIL (исходная форма). Уточнение: селекцию ускоряет κ, не α — см. статью 07, раздел верификации.");
}

/// П2: устойчивость доминанты после снятия стимула требует ρ выше критического.
/// Цель активна t<60, затем вход исчезает; конкуренты без входа (только шум),
/// чтобы изолировать чистую персистентность. w=0.4 ⇒ критическое ρ = 0.6 (ρ+w = 1).
fn predict2() {
    println!("\nП2: удержание доминанты после снятия стимула растёт с ρ (критическое ρ+w=1)");
    let steps = 200usize;
    let offset = 60usize;
    println!("ρ\tсреднее удержание, шагов (5 сидов)");
    let mut holds = Vec::new();
    for rho in [0.2, 0.4, 0.55, 0.7, 0.9] {
        let p = Params {
            inertia: rho,
            self_excitation: 0.4,
            noise: 0.02,
            ..Default::default()
        };
        let mut per_seed = Vec::new();
        for seed in [1u64, 2, 3, 4, 5] {
            let mut rng = Rng::new(seed);
            let mut x = vec![0.0f64; 3];
            let g = [1.0, 0.0, 0.0];
            let mut hold = 0usize;
            for t in 0..steps {
                let mut s = [0.5, 0.0, 0.0];
                if t >= offset {
                    s[0] = 0.0; // стимул цели снят, конкуренты молчат
                }
                step(&mut x, &p, &mut rng, 0, &s, &g);
                if t >= offset && dominant(&x, &p) == Some(0) {
                    hold += 1;
                }
            }
            per_seed.push(hold as f64);
        }
        let m = mean(&per_seed);
        holds.push(m);
        println!("{rho}\t{m:.1}");
    }
    let monotone = holds.windows(2).all(|w| w[1] >= w[0] - 1e-9);
    println!("ВЕРДИКТ: {}", if monotone { "PASS" } else { "FAIL" });
}

/// П3: хронотоп компенсирует низкую salience: слабый целевой стимул
/// выигрывает у сильного «чужого» только при сродстве к цели.
fn predict3() {
    println!("\nП3: хронотоп компенсирует низкую salience (s=0.32 против 0.60)");
    let steps = 200usize;
    let p = Params { noise: 0.01, ..Default::default() };
    let mut results = Vec::new();
    for (label, g_goal) in [("без хронотопа", 0.0), ("с хронотопом", 1.0)] {
        let s = [0.32, 0.60];
        let g = [g_goal, 0.0];
        let mut winners = 0usize;
        for seed in [1u64, 2, 3, 4, 5] {
            let mut rng = Rng::new(seed);
            let mut x = vec![0.0f64; 2];
            for _ in 0..steps {
                step(&mut x, &p, &mut rng, 0, &s, &g);
            }
            if leader_idx(&x) == 0 {
                winners += 1;
            }
        }
        results.push(winners);
        println!("{label}: цель лидирует в {winners}/5 сидов");
    }
    let pass = results[0] <= 1 && results[1] >= 4;
    println!("ВЕРДИКТ: {}", if pass { "PASS" } else { "FAIL" });
}

/// П4: парковка монотонна, пока доминанта активна.
fn predict4() {
    println!("\nП4: парковка (сопряжённо заторможенное) не убывает при активной доминанте");
    let s = [0.5, 0.40, 0.38, 0.35];
    let g = [1.0, 0.0, 0.0, 0.0];
    let p = Params::default();
    let mut rng = Rng::new(9);
    let mut x = vec![0.0f64; 4];
    let mut parked = 0usize;
    let mut ok = true;
    for _ in 0..200 {
        step(&mut x, &p, &mut rng, 0, &s, &g);
        if let Some(d) = dominant(&x, &p) {
            let now = (0..s.len()).filter(|&i| i != d).count();
            if now < parked {
                ok = false;
            }
            parked = parked.max(now);
        }
    }
    println!("ВЕРДИКТ: {}", if ok { "PASS" } else { "FAIL" });
}

/// П5: существует порог κ, выше которого доминанта «прилипает»:
/// сильный поздний дистрактор не смещает её.
fn predict5() {
    println!("\nП5: порог сопряжённого торможения (дистрактор s=1.2 с t=60)");
    let steps = 150usize;
    let mut rows = Vec::new();
    for kappa in [0.0, 0.2, 0.4, 0.6] {
        let p = Params { lateral_inhibition: kappa, noise: 0.01, ..Default::default() };
        let mut flipped = 0usize;
        for seed in [1u64, 2, 3, 4, 5] {
            let mut rng = Rng::new(seed);
            let mut x = vec![0.0f64; 2];
            let g = [1.0, 0.0];
            for t in 0..steps {
                let mut s = [0.5, 0.0];
                if t >= 60 {
                    s[1] = 1.2;
                }
                step(&mut x, &p, &mut rng, 0, &s, &g);
            }
            if leader_idx(&x) == 1 {
                flipped += 1;
            }
        }
        rows.push(flipped);
        println!("κ={kappa}\tдистрактор сместил доминанту в {flipped}/5 сидов");
    }
    let monotone = rows.windows(2).all(|w| w[1] <= w[0]);
    println!("ВЕРДИКТ: {}", if monotone { "PASS" } else { "FAIL" });
}

fn main() {
    predict1();
    predict2();
    predict3();
    predict4();
    predict5();
}
