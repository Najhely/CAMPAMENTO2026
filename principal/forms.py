from django import forms
from .models import Publicacion, Grupo, Actividad, Noticia
from .models import Inscripcion, HistorialPuntos, Usuario, InventarioGlobal, Iglesia, Union
from django.db.models import Q
from decimal import Decimal

class PublicacionForm(forms.ModelForm):
    class Meta:
        model = Publicacion
        fields = ['archivo', 'referencia']
        widgets = {
            'referencia': forms.Textarea(attrs={
                'rows': 2, 
                'placeholder': '¿Qué está pasando en el campamento?', 
                'class': 'w-full p-3 rounded-xl border-none ring-1 ring-stone-200 focus:ring-emerald-500 text-sm'
            }),
            'archivo': forms.FileInput(attrs={'class': 'hidden', 'id': 'file-upload'}),
        }

# ========== FORMULARIO UNIFICADO PARA 1 O 2 PERSONAS ==========
class InscripcionUnificadoForm(forms.Form):
    """Formulario unificado para inscribir 1 o 2 personas"""
    
    # ========== CAMPOS COMUNES ==========
    inscripcion_tipo = forms.ChoiceField(
        choices=[
            ('simple', 'Inscripción Simple (1 persona)'),
            ('doble', 'Inscripción Doble (2 personas)'),
        ],
        initial='simple',
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio h-4 w-4 text-blue-600',
            'onchange': 'cambiarTipoInscripcion(this.value)'
        }),
        label='Tipo de inscripción'
    )
    
    # ========== PERSONA 1 (SIEMPRE REQUERIDA) ==========
    nombre_persona = forms.CharField(
        max_length=200,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Nombre completo de la persona'
        })
    )
    
    iglesia = forms.ModelChoiceField(
        queryset=Iglesia.objects.all().order_by('nombre'),
        required=True,
        label='Iglesia',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    union = forms.ModelChoiceField(
        queryset=Union.objects.all().order_by('nombre'),
        required=False,
        label='Unión (opcional)',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    sexo = forms.ChoiceField(
        choices=[('', '--- Seleccionar ---'), ('M', 'Masculino'), ('F', 'Femenino')],
        required=True,
        label='Sexo',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    edad = forms.IntegerField(
        min_value=1,
        max_value=100,
        required=True,
        label='Edad',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'min': '1',
            'max': '100'
        })
    )
    
    talla_polera = forms.ChoiceField(
        required=False,
        label='Talla de polera preferida',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    # ========== FINANZAS PERSONA 1 ==========
    costo_total = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=89.00,
        label='Costo total ($)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'value': '89.00'
        })
    )
    
    descuento = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0.00,
        label='Descuento (%)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'value': '0.00',
            'onchange': 'calcularFinanzas(1)'
        })
    )
    
    paga = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Monto pagado ($)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'placeholder': '0.00',
            'onchange': 'calcularFinanzas(1)'
        })
    )
    
    # Campos calculados (solo lectura)
    precio_final = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Precio final ($)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg bg-gray-50',
            'readonly': 'readonly',
            'value': '89.00'
        })
    )
    
    cambio = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Cambio ($)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg bg-gray-50',
            'readonly': 'readonly',
            'value': '0.00'
        })
    )
    
    # ========== CAMPOS PARA PERSONA 2 (OPCIONALES) ==========
    # Estos se mostrarán solo cuando inscripcion_tipo == 'doble'
    nombre_persona_2 = forms.CharField(
        max_length=200,
        required=False,
        label='Nombre completo (Persona 2)',
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2',
            'placeholder': 'Nombre completo de la segunda persona'
        })
    )
    
    iglesia_2 = forms.ModelChoiceField(
        queryset=Iglesia.objects.all().order_by('nombre'),
        required=False,
        label='Iglesia (Persona 2)',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2'
        })
    )
    
    union_2 = forms.ModelChoiceField(
        queryset=Union.objects.all().order_by('nombre'),
        required=False,
        label='Unión (Persona 2)',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2'
        })
    )
    
    sexo_2 = forms.ChoiceField(
        choices=[('', '--- Seleccionar ---'), ('M', 'Masculino'), ('F', 'Femenino')],
        required=False,
        label='Sexo (Persona 2)',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2'
        })
    )
    
    edad_2 = forms.IntegerField(
        min_value=1,
        max_value=100,
        required=False,
        label='Edad (Persona 2)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2',
            'min': '1',
            'max': '100'
        })
    )
    
    talla_polera_2 = forms.ChoiceField(
        required=False,
        label='Talla de polera (Persona 2)',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2'
        })
    )
    
    # ========== FINANZAS PERSONA 2 ==========
    costo_total_2 = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=89.00,
        required=False,
        label='Costo total ($) - Persona 2',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2',
            'step': '0.01',
            'value': '89.00'
        })
    )
    
    descuento_2 = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0.00,
        required=False,
        label='Descuento (%) - Persona 2',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2',
            'step': '0.01',
            'value': '0.00',
            'onchange': 'calcularFinanzas(2)'
        })
    )
    
    paga_2 = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Monto pagado ($) - Persona 2',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 persona-2',
            'step': '0.01',
            'placeholder': '0.00',
            'onchange': 'calcularFinanzas(2)'
        })
    )
    
    precio_final_2 = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Precio final ($) - Persona 2',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg bg-gray-50 persona-2',
            'readonly': 'readonly',
            'value': '89.00'
        })
    )
    
    cambio_2 = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Cambio ($) - Persona 2',
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg bg-gray-50 persona-2',
            'readonly': 'readonly',
            'value': '0.00'
        })
    )
    
    # ========== CAMPOS PARA ASIGNACIÓN DE GRUPO ==========
    asignar_grupo_auto = forms.BooleanField(
        initial=True,
        required=False,
        label='Asignar grupo automáticamente',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
            'onchange': 'toggleGrupoManual()'
        })
    )
    
    grupo_manual = forms.ModelChoiceField(
        queryset=Grupo.objects.all().order_by('nombre'),
        required=False,
        label='Seleccionar grupo manualmente',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 grupo-manual',
            'disabled': 'disabled'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener tallas disponibles del inventario
        tallas_disponibles = InventarioGlobal.objects.filter(
            articulo='polera',
            stock_actual__gt=0
        ).values_list('talla', flat=True).distinct()
        
        # Crear opciones para tallas
        opciones_tallas = [('', '--- Seleccionar talla ---')]
        for talla in sorted(tallas_disponibles):
            opciones_tallas.append((talla, f"Talla {talla}"))
        
        self.fields['talla_polera'].choices = opciones_tallas
        self.fields['talla_polera_2'].choices = opciones_tallas
        
        # Configurar valores iniciales para campos calculados
        self.initial['precio_final'] = 89.00
        self.initial['cambio'] = 0.00
        self.initial['precio_final_2'] = 89.00
        self.initial['cambio_2'] = 0.00
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_inscripcion = cleaned_data.get('inscripcion_tipo', 'simple')
        
        if tipo_inscripcion == 'doble':
            # Validar campos requeridos para persona 2
            campos_requeridos_p2 = [
                'nombre_persona_2', 'iglesia_2', 'sexo_2', 'edad_2'
            ]
            
            for campo in campos_requeridos_p2:
                if not cleaned_data.get(campo):
                    self.add_error(campo, f'Este campo es obligatorio para inscripción doble')
            
            # Validar que no sean el mismo nombre
            nombre1 = cleaned_data.get('nombre_persona', '').strip()
            nombre2 = cleaned_data.get('nombre_persona_2', '').strip()
            
            if nombre1 and nombre2 and nombre1.lower() == nombre2.lower():
                self.add_error('nombre_persona_2', 'Las personas no pueden tener el mismo nombre')
            
            # Validar que haya stock para 2 poleras si se especifican tallas
            talla1 = cleaned_data.get('talla_polera')
            talla2 = cleaned_data.get('talla_polera_2')
            
            if talla1 and talla2:
                # Verificar stock para ambas tallas
                stock_talla1 = InventarioGlobal.objects.filter(
                    articulo='polera',
                    talla=talla1,
                    stock_actual__gt=0
                ).count()
                
                stock_talla2 = InventarioGlobal.objects.filter(
                    articulo='polera',
                    talla=talla2,
                    stock_actual__gt=0
                ).count()
                
                if stock_talla1 < 1:
                    self.add_error('talla_polera', f'No hay stock disponible para talla {talla1}')
                if stock_talla2 < 1:
                    self.add_error('talla_polera_2', f'No hay stock disponible para talla {talla2}')
        
        # Validar finanzas para persona 1
        costo1 = cleaned_data.get('costo_total', Decimal('0'))
        desc1 = cleaned_data.get('descuento', Decimal('0'))
        paga1 = cleaned_data.get('paga', Decimal('0'))
        
        if desc1 < 0 or desc1 > 100:
            self.add_error('descuento', 'El descuento debe estar entre 0 y 100%')
        
        # Calcular precio final y cambio para persona 1
        if costo1 and desc1:
            precio_final1 = costo1 * (Decimal('1') - (desc1 / Decimal('100')))
            cleaned_data['precio_final'] = precio_final1.quantize(Decimal('0.01'))
            cleaned_data['cambio'] = (paga1 - precio_final1).quantize(Decimal('0.01'))
        
        # Validar finanzas para persona 2 (si aplica)
        if tipo_inscripcion == 'doble':
            costo2 = cleaned_data.get('costo_total_2', Decimal('0'))
            desc2 = cleaned_data.get('descuento_2', Decimal('0'))
            paga2 = cleaned_data.get('paga_2', Decimal('0'))
            
            if desc2 < 0 or desc2 > 100:
                self.add_error('descuento_2', 'El descuento debe estar entre 0 y 100%')
            
            if costo2 and desc2:
                precio_final2 = costo2 * (Decimal('1') - (desc2 / Decimal('100')))
                cleaned_data['precio_final_2'] = precio_final2.quantize(Decimal('0.01'))
                cleaned_data['cambio_2'] = (paga2 - precio_final2).quantize(Decimal('0.01'))
        
        return cleaned_data
    
    def get_persona1_data(self):
        """Extrae datos de persona 1 del formulario"""
        return {
            'nombre_persona': self.cleaned_data.get('nombre_persona'),
            'iglesia': self.cleaned_data.get('iglesia'),
            'union': self.cleaned_data.get('union'),
            'sexo': self.cleaned_data.get('sexo'),
            'edad': self.cleaned_data.get('edad'),
            'talla_polera': self.cleaned_data.get('talla_polera'),
            'costo_total': self.cleaned_data.get('costo_total'),
            'descuento': self.cleaned_data.get('descuento'),
            'paga': self.cleaned_data.get('paga'),
            'precio_final': self.cleaned_data.get('precio_final'),
            'cambio': self.cleaned_data.get('cambio'),
        }
    
    def get_persona2_data(self):
        """Extrae datos de persona 2 del formulario (solo si es doble)"""
        if self.cleaned_data.get('inscripcion_tipo') != 'doble':
            return None
        
        return {
            'nombre_persona': self.cleaned_data.get('nombre_persona_2'),
            'iglesia': self.cleaned_data.get('iglesia_2'),
            'union': self.cleaned_data.get('union_2'),
            'sexo': self.cleaned_data.get('sexo_2'),
            'edad': self.cleaned_data.get('edad_2'),
            'talla_polera': self.cleaned_data.get('talla_polera_2'),
            'costo_total': self.cleaned_data.get('costo_total_2'),
            'descuento': self.cleaned_data.get('descuento_2'),
            'paga': self.cleaned_data.get('paga_2'),
            'precio_final': self.cleaned_data.get('precio_final_2'),
            'cambio': self.cleaned_data.get('cambio_2'),
        }
    
    def get_grupo_seleccionado(self):
        """Obtiene el grupo seleccionado (automático o manual)"""
        if self.cleaned_data.get('asignar_grupo_auto'):
            return None  # Se asignará automáticamente en la vista
        else:
            return self.cleaned_data.get('grupo_manual')

# ========== FORMULARIO ANTERIOR PARA COMPATIBILIDAD ==========
class InscripcionForm(forms.ModelForm):
    """Formulario antiguo para compatibilidad - será deprecado"""
    talla_polera = forms.ChoiceField(
        required=False,
        label='Talla preferida de polera',
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        help_text="Selecciona la talla preferida (opcional)"
    )
    
    class Meta:
        model = Inscripcion
        fields = [
            'nombre_persona', 'iglesia', 'union', 'sexo', 'edad', 
            'costo_total', 'descuento', 'paga'
        ]
        widgets = {
            'nombre_persona': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'iglesia': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'union': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'sexo': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'edad': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'costo_total': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'descuento': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'step':'0.01'}),
            'paga': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Monto pagado'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener tallas disponibles del inventario
        tallas_disponibles = InventarioGlobal.objects.filter(
            articulo='polera',
            stock_actual__gt=0
        ).values_list('talla', flat=True).distinct()
        
        # Crear opciones para el campo talla_polera
        opciones = [('', '--- Seleccionar talla ---')]
        for talla in sorted(tallas_disponibles):
            opciones.append((talla, f"Talla {talla}"))
        
        self.fields['talla_polera'].choices = opciones

class HistorialPuntosForm(forms.ModelForm):
    class Meta:
        model = HistorialPuntos
        fields = ['grupo', 'cantidad', 'motivo']
        widgets = {
            'grupo': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Puntos a sumar'}),
            'motivo': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Motivo (ej: Ganó juego, asistencia)'}),
        }

class UsuarioCrearForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Contraseña'}),
        required=True,
        label='Contraseña'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Confirmar contraseña'}),
        required=True,
        label='Confirmar contraseña'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'correo@ejemplo.com'}),
            'rol': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UsuarioEditarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['email', 'rol', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded'}),
            'rol': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Apellido'}),
        }


class InventarioForm(forms.ModelForm):
    """
    Formulario simplificado para inventario.
    Los colores se seleccionan de grupos existentes mediante el template.
    """
    
    class Meta:
        model = InventarioGlobal
        fields = ['articulo', 'talla', 'stock_actual']
        widgets = {
            'articulo': forms.Select(attrs={
                'class': 'w-full p-3 border border-stone-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'id': 'id_articulo'
            }),
            'talla': forms.Select(attrs={
                'class': 'w-full p-3 border border-stone-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'id': 'id_talla'
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'w-full p-3 border border-stone-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
                'placeholder': 'Cantidad en stock',
                'id': 'id_stock_actual'
            }),
        }
        labels = {
            'articulo': 'Tipo de Artículo',
            'talla': 'Talla',
            'stock_actual': 'Cantidad en Stock'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos requeridos
        for field_name in self.fields:
            self.fields[field_name].required = True
    
class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nombre', 'color_nombre', 'color_hex', 'insignia', 
                  'min_age', 'max_age', 'sexo', 'union']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Nombre del grupo'}),
            'color_nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Ej: Rojo, Azul, Verde'}),
            'color_hex': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'type': 'color', 'value': '#FF0000'}),
            'insignia': forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}),
            'min_age': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Edad mínima'}),
            'max_age': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Edad máxima'}),
            'sexo': forms.Select(attrs={'class': 'w-full p-2 border rounded'}, 
                                choices=[('', '--- Seleccionar ---'), ('M', 'Masculino'), ('F', 'Femenino'), ('X', 'Mixto')]),
            'union': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Unión asociada'}),
        }
        help_texts = {
            'color_hex': 'Selecciona el color del equipo',
            'color_nombre': 'Nombre descriptivo del color',
        }

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'hora_inicio', 'ubicacion', 'es_obligatoria']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Título de la actividad'}),
            'hora_inicio': forms.DateTimeInput(attrs={'class': 'w-full p-2 border rounded', 'type': 'datetime-local'}),
            'ubicacion': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Ubicación'}),
            'es_obligatoria': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
        }

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Título de la noticia'}),
            'contenido': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 5, 'placeholder': 'Contenido de la noticia'}),
        }

class UnionForm(forms.ModelForm):
    class Meta:
        model = Union
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Nombre de la unión'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción (opcional)'
            }),
        }

class IglesiaForm(forms.ModelForm):
    class Meta:
        model = Iglesia
        fields = ['nombre', 'ubicacion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Nombre de la iglesia'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Ubicación (opcional)'
            }),
        }