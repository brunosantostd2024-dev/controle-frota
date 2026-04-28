from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fleetcontrol.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ── MODELS ──
class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(100), nullable=False)
    placa       = db.Column(db.String(20), unique=True, nullable=False)
    tipo        = db.Column(db.String(50))
    combustivel = db.Column(db.String(50))
    km          = db.Column(db.Float, default=0)
    media_esp   = db.Column(db.Float, default=10)
    ano         = db.Column(db.Integer)
    motorista   = db.Column(db.String(100))
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'nome': self.nome, 'placa': self.placa,
            'tipo': self.tipo, 'combustivel': self.combustivel,
            'km': self.km, 'media_esp': self.media_esp,
            'ano': self.ano, 'motorista': self.motorista,
            'criado_em': self.criado_em.isoformat()
        }

class Abastecimento(db.Model):
    __tablename__ = 'abastecimentos'
    id          = db.Column(db.Integer, primary_key=True)
    veiculo_id  = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    data        = db.Column(db.String(20))
    km          = db.Column(db.Float)
    km_anterior = db.Column(db.Float)
    litros      = db.Column(db.Float)
    preco       = db.Column(db.Float)
    total       = db.Column(db.Float)
    kml         = db.Column(db.Float)
    posto       = db.Column(db.String(200))
    motorista   = db.Column(db.String(100))
    tipo        = db.Column(db.String(50))
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'veiculo_id': self.veiculo_id,
            'data': self.data, 'km': self.km, 'km_anterior': self.km_anterior,
            'litros': self.litros, 'preco': self.preco, 'total': self.total,
            'kml': self.kml, 'posto': self.posto,
            'motorista': self.motorista, 'tipo': self.tipo,
            'criado_em': self.criado_em.isoformat()
        }

# ── ROUTES ──
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/veiculos', methods=['GET'])
def get_veiculos():
    return jsonify([v.to_dict() for v in Veiculo.query.order_by(Veiculo.nome).all()])

@app.route('/api/veiculos', methods=['POST'])
def add_veiculo():
    d = request.json
    v = Veiculo(
        nome=d['nome'], placa=d['placa'].upper(),
        tipo=d.get('tipo','carro'), combustivel=d.get('combustivel','flex'),
        km=float(d.get('km',0)), media_esp=float(d.get('media_esp',10)),
        ano=int(d.get('ano', datetime.now().year)),
        motorista=d.get('motorista','')
    )
    db.session.add(v)
    db.session.commit()
    return jsonify(v.to_dict()), 201

@app.route('/api/veiculos/<int:vid>', methods=['PUT'])
def update_veiculo(vid):
    v = Veiculo.query.get_or_404(vid)
    d = request.json
    for field in ['nome','placa','tipo','combustivel','km','media_esp','ano','motorista']:
        if field in d:
            setattr(v, field, d[field])
    db.session.commit()
    return jsonify(v.to_dict())

@app.route('/api/veiculos/<int:vid>', methods=['DELETE'])
def delete_veiculo(vid):
    v = Veiculo.query.get_or_404(vid)
    db.session.delete(v)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/abastecimentos', methods=['GET'])
def get_abastecimentos():
    return jsonify([a.to_dict() for a in Abastecimento.query.order_by(Abastecimento.data.desc()).all()])

@app.route('/api/abastecimentos', methods=['POST'])
def add_abastecimento():
    d = request.json
    litros = float(d.get('litros', 0))
    preco  = float(d.get('preco', 0))
    km     = float(d.get('km', 0))
    km_ant = float(d.get('km_anterior', 0))
    total  = round(litros * preco, 2)
    kml    = round((km - km_ant) / litros, 2) if litros > 0 and km > km_ant else None

    a = Abastecimento(
        veiculo_id=int(d['veiculo_id']), data=d.get('data',''),
        km=km, km_anterior=km_ant, litros=litros, preco=preco,
        total=total, kml=kml,
        posto=d.get('posto',''), motorista=d.get('motorista',''),
        tipo=d.get('tipo','completo')
    )
    db.session.add(a)

    # Atualiza hodômetro do veículo
    v = Veiculo.query.get(int(d['veiculo_id']))
    if v and km > v.km:
        v.km = km

    db.session.commit()
    return jsonify(a.to_dict()), 201

@app.route('/api/abastecimentos/<int:aid>', methods=['DELETE'])
def delete_abastecimento(aid):
    a = Abastecimento.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    veiculos = Veiculo.query.all()
    abastecimentos = Abastecimento.query.all()
    total_l = sum(a.litros or 0 for a in abastecimentos)
    total_r = sum(a.total or 0 for a in abastecimentos)
    kmls = [a.kml for a in abastecimentos if a.kml]
    media_g = round(sum(kmls)/len(kmls), 2) if kmls else 0
    return jsonify({
        'total_veiculos': len(veiculos),
        'total_litros': round(total_l, 1),
        'total_custo': round(total_r, 2),
        'media_kml': media_g,
        'total_abastecimentos': len(abastecimentos)
    })

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
