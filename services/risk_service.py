def clasificar_imc(peso_kg, altura_cm):
    imc = float(peso_kg) / ((float(altura_cm) / 100) ** 2)
    if imc < 18.5:
        return imc, "Bajo peso"
    if imc < 25:
        return imc, "Normal"
    if imc < 30:
        return imc, "Sobrepeso"
    return imc, "Obesidad"


def calcular_riesgo_integral(
    imc,
    estrato,
    actividad_minutos,
    calidad_alimentacion,
    bebidas_azucaradas,
    horas_sueno,
    horas_pantalla,
    antecedentes_familiares,
    acceso_espacios,
):
    puntaje = 0
    estrato = int(estrato)
    actividad_minutos = int(actividad_minutos)
    horas_sueno = float(horas_sueno)
    horas_pantalla = float(horas_pantalla)

    if imc < 18.5 or 25 <= imc < 30:
        puntaje += 2
    elif imc >= 30:
        puntaje += 4

    if estrato <= 2:
        puntaje += 2
    elif estrato == 3:
        puntaje += 1

    if actividad_minutos < 60:
        puntaje += 3
    elif actividad_minutos < 150:
        puntaje += 2

    if calidad_alimentacion == "Baja":
        puntaje += 2
    elif calidad_alimentacion == "Media":
        puntaje += 1

    if bebidas_azucaradas == "Diario":
        puntaje += 2
    elif bebidas_azucaradas == "3-5 veces/semana":
        puntaje += 1

    if horas_sueno < 6 or horas_sueno > 10:
        puntaje += 2
    elif horas_sueno < 7:
        puntaje += 1

    if horas_pantalla >= 6:
        puntaje += 2
    elif horas_pantalla >= 4:
        puntaje += 1

    if antecedentes_familiares == "Si":
        puntaje += 2

    if acceso_espacios == "No tiene":
        puntaje += 2
    elif acceso_espacios == "Limitado":
        puntaje += 1

    if puntaje >= 11:
        return puntaje, "ALTO"
    if puntaje >= 6:
        return puntaje, "MODERADO"
    return puntaje, "BAJO"
