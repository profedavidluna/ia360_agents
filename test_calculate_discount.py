"""Tests para calculate_discount"""

import pytest
from commerce_module import calculate_discount


def test_regular_customer_no_discount():
	"""Test: Cliente regular no recibe descuento"""
	# Entrada
	inputs = {'price': 100.0, 'customer_type': 'regular'}
	
	# Ejecutar
	result = calculate_discount(**inputs)
	
	# Verificar
	assert result == 100.0, f"Esperado 100.0, obtuvo {result}"

def test_vip_customer_10_percent_discount():
	"""Test: Cliente VIP recibe 10% de descuento"""
	# Entrada
	inputs = {'price': 100.0, 'customer_type': 'vip'}
	
	# Ejecutar
	result = calculate_discount(**inputs)
	
	# Verificar
	assert result == 90.0, f"Esperado 90.0, obtuvo {result}"

def test_corporate_customer_15_percent_discount():
	"""Test: Cliente corporativo recibe 15% de descuento"""
	# Entrada
	inputs = {'price': 100.0, 'customer_type': 'corporate'}
	
	# Ejecutar
	result = calculate_discount(**inputs)
	
	# Verificar
	assert result == 85.0, f"Esperado 85.0, obtuvo {result}"

def test_zero_price_edge_case():
	"""Test: Precio cero con cliente VIP retorna cero"""
	# Entrada (caso límite)
	inputs = {'price': 0.0, 'customer_type': 'vip'}
	
	# Ejecutar
	result = calculate_discount(**inputs)
	
	# Verificar comportamiento en caso límite
	assert result == 0.0

def test_negative_price_raises_error():
	"""Test: Precio negativo lanza ValueError"""
	# Verificar que lanza excepción
	with pytest.raises(ValueError):
		inputs = {'price': -50.0, 'customer_type': 'regular'}
		calculate_discount(**inputs)

