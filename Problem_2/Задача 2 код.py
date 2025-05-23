import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.integrate import solve_ivp

# Параметры Земли и орбиты
R_earth = 6371302  # м
mu = 398600.4415e9  # м^3/с^2
omega_earth = 7.29211e-5  # рад/с
J2 = 1082.8e-6

h = 600000  # высота орбиты (м)
a = R_earth + h  # большая полуось (м)
i = np.radians(98)  # наклонение (рад)
e = 0  # эксцентриситет (круговая орбита)

# Период орбиты 
T = 2 * np.pi * np.sqrt(a**3 / mu)  # сек

# Количество спутников
N_satellites = 14

# Время моделирования (122 витка)
t_span = (0, 122 * T)  # 122 орбитальных периода
t_eval = np.linspace(0, 3 * T, 1000)  # точки для вывода

# Функция для вычисления производных 
def orbit_dynamics(t, y, mu):
    r = y[:3]
    v = y[3:]
    r_norm = np.linalg.norm(r)
    drdt = v
    dvdt = -mu * r / r_norm**3
    return np.concatenate([drdt, dvdt])

# Функция для вычисления точки
def compute_ground_track(r, t):
    # Преобразование в сферические координаты (долгота, широта)
    x, y, z = r
    lambda_ = np.arctan2(y, x)  # долгота (рад)
    phi = np.arctan2(z, np.sqrt(x**2 + y**2))  # широта (рад)
    
    # Учет вращения Земли
    lambda_earth = lambda_ - omega_earth * t
    lambda_earth = np.mod(lambda_earth + np.pi, 2 * np.pi) - np.pi  # [-π, π]
    
    return np.degrees(lambda_earth), np.degrees(phi)

# Создание карты
def plot_ground_tracks(ground_tracks):
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.gridlines()
    
    for k in range(N_satellites):
        lambda_earth, phi = ground_tracks[k]
        ax.plot(lambda_earth, phi, '-', linewidth=1, transform=ccrs.PlateCarree(),
                label=f'Спутник {k+1}' if k < 15 else None)
    
    plt.title('Граундтреки (122 витка, 14 спутников)')
    plt.legend(loc='upper right')
    plt.show()

# Моделирование для каждого спутника
ground_tracks = []

for k in range(N_satellites):
    # Начальные условия (орбита в плоскости XY, восходящий узел разнесен)
    Omega_k = np.radians(k * 360 / N_satellites)  # долгота восходящего узла
    
    # Начальное положение (в перицентре)
    r0 = np.array([a * np.cos(Omega_k), a * np.sin(Omega_k), 0])
    
    # Начальная скорость (наклонение i)
    v0 = np.sqrt(mu / a) * np.array([-np.sin(Omega_k) * np.cos(i),
                                     np.cos(Omega_k) * np.cos(i),
                                     np.sin(i)])
    
    # Решение ОДУ 
    sol = solve_ivp(orbit_dynamics, t_span, np.concatenate([r0, v0]),
                    args=(mu,), t_eval=t_eval, rtol=1e-8)
    
    # Вычисление подспутниковых точек
    lambda_earth, phi = [], []
    for t, r in zip(sol.t, sol.y[:3].T):
        lambda_, phi_ = compute_ground_track(r, t)
        lambda_earth.append(lambda_)
        phi.append(phi_)
    
    ground_tracks.append((lambda_earth, phi))

# Визуализация
plot_ground_tracks(ground_tracks)