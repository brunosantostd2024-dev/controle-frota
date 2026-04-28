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

class Manutencao(db.Model):
    __tablename__ = 'manutencoes'
    id           = db.Column(db.Integer, primary_key=True)
    veiculo_id   = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    tipo         = db.Column(db.String(100), nullable=False)   # ex: troca de óleo, revisão
    descricao    = db.Column(db.String(500))
    data         = db.Column(db.String(20))                    # data realizada
    km           = db.Column(db.Float)                         # km na realização
    custo        = db.Column(db.Float, default=0)
    oficina      = db.Column(db.String(200))
    # Agendamento
    proxima_data = db.Column(db.String(20))                    # próxima data prevista
    proxima_km   = db.Column(db.Float)                         # próximo km previsto
    status       = db.Column(db.String(20), default='realizada')  # realizada | agendada
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'veiculo_id': self.veiculo_id,
            'tipo': self.tipo, 'descricao': self.descricao,
            'data': self.data, 'km': self.km, 'custo': self.custo,
            'oficina': self.oficina, 'proxima_data': self.proxima_data,
            'proxima_km': self.proxima_km, 'status': self.status,
            'criado_em': self.criado_em.isoformat()
        }

class DocumentoVeiculo(db.Model):
    __tablename__ = 'documentos'
    id           = db.Column(db.Integer, primary_key=True)
    veiculo_id   = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    tipo         = db.Column(db.String(50), nullable=False)    # ipva | seguro | licenciamento | cnh
    vencimento   = db.Column(db.String(20), nullable=False)
    valor        = db.Column(db.Float, default=0)
    pago         = db.Column(db.Boolean, default=False)
    observacao   = db.Column(db.String(300))
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'veiculo_id': self.veiculo_id,
            'tipo': self.tipo, 'vencimento': self.vencimento,
            'valor': self.valor, 'pago': self.pago,
            'observacao': self.observacao,
            'criado_em': self.criado_em.isoformat()
        }

class Equipe(db.Model):
    __tablename__ = 'equipes'
    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(300))
    ativa     = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'nome': self.nome,
            'descricao': self.descricao, 'ativa': self.ativa,
            'criado_em': self.criado_em.isoformat()
        }

class Diaria(db.Model):
    __tablename__ = 'diarias'
    id          = db.Column(db.Integer, primary_key=True)
    equipe_id   = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    veiculo_id  = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=True)
    colaborador = db.Column(db.String(100), nullable=False)
    data_inicio = db.Column(db.String(20), nullable=False)
    data_fim    = db.Column(db.String(20), nullable=False)
    qtd_dias    = db.Column(db.Float, default=1)
    valor_dia   = db.Column(db.Float, default=0)
    total       = db.Column(db.Float, default=0)
    destino     = db.Column(db.String(200))
    motivo      = db.Column(db.String(300))
    status      = db.Column(db.String(20), default='pendente')  # pendente | aprovado | pago | cancelado
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'equipe_id': self.equipe_id,
            'veiculo_id': self.veiculo_id,
            'colaborador': self.colaborador,
            'data_inicio': self.data_inicio, 'data_fim': self.data_fim,
            'qtd_dias': self.qtd_dias, 'valor_dia': self.valor_dia,
            'total': self.total, 'destino': self.destino,
            'motivo': self.motivo, 'status': self.status,
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
    # Remove registros vinculados antes de deletar o veículo
    Abastecimento.query.filter_by(veiculo_id=vid).delete()
    Manutencao.query.filter_by(veiculo_id=vid).delete()
    DocumentoVeiculo.query.filter_by(veiculo_id=vid).delete()
    # Diárias: apenas remove o vínculo com o veículo
    Diaria.query.filter_by(veiculo_id=vid).update({'veiculo_id': None})
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

# ── MANUTENÇÕES ──
@app.route('/api/manutencoes', methods=['GET'])
def get_manutencoes():
    vid = request.args.get('veiculo_id')
    q = Manutencao.query
    if vid:
        q = q.filter_by(veiculo_id=int(vid))
    return jsonify([m.to_dict() for m in q.order_by(Manutencao.data.desc()).all()])

@app.route('/api/manutencoes', methods=['POST'])
def add_manutencao():
    d = request.json
    m = Manutencao(
        veiculo_id=int(d['veiculo_id']),
        tipo=d.get('tipo',''),
        descricao=d.get('descricao',''),
        data=d.get('data',''),
        km=float(d.get('km',0)) if d.get('km') else None,
        custo=float(d.get('custo',0)),
        oficina=d.get('oficina',''),
        proxima_data=d.get('proxima_data',''),
        proxima_km=float(d.get('proxima_km',0)) if d.get('proxima_km') else None,
        status=d.get('status','realizada')
    )
    db.session.add(m)
    db.session.commit()
    return jsonify(m.to_dict()), 201

@app.route('/api/manutencoes/<int:mid>', methods=['DELETE'])
def delete_manutencao(mid):
    m = Manutencao.query.get_or_404(mid)
    db.session.delete(m)
    db.session.commit()
    return jsonify({'ok': True})

# ── DOCUMENTOS (IPVA, SEGURO etc) ──
@app.route('/api/documentos', methods=['GET'])
def get_documentos():
    return jsonify([doc.to_dict() for doc in DocumentoVeiculo.query.order_by(DocumentoVeiculo.vencimento).all()])

@app.route('/api/documentos', methods=['POST'])
def add_documento():
    d = request.json
    doc = DocumentoVeiculo(
        veiculo_id=int(d['veiculo_id']),
        tipo=d.get('tipo','ipva'),
        vencimento=d.get('vencimento',''),
        valor=float(d.get('valor',0)),
        pago=bool(d.get('pago', False)),
        observacao=d.get('observacao','')
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify(doc.to_dict()), 201

@app.route('/api/documentos/<int:did>', methods=['PUT'])
def update_documento(did):
    doc = DocumentoVeiculo.query.get_or_404(did)
    d = request.json
    for field in ['tipo','vencimento','valor','pago','observacao']:
        if field in d:
            setattr(doc, field, d[field])
    db.session.commit()
    return jsonify(doc.to_dict())

@app.route('/api/documentos/<int:did>', methods=['DELETE'])
def delete_documento(did):
    doc = DocumentoVeiculo.query.get_or_404(did)
    db.session.delete(doc)
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

# ── EQUIPES ──
@app.route('/api/equipes', methods=['GET'])
def get_equipes():
    return jsonify([e.to_dict() for e in Equipe.query.order_by(Equipe.nome).all()])

@app.route('/api/equipes', methods=['POST'])
def add_equipe():
    d = request.json
    e = Equipe(
        nome=d['nome'],
        descricao=d.get('descricao', ''),
        ativa=bool(d.get('ativa', True))
    )
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201

@app.route('/api/equipes/<int:eid>', methods=['PUT'])
def update_equipe(eid):
    e = Equipe.query.get_or_404(eid)
    d = request.json
    for field in ['nome', 'descricao', 'ativa']:
        if field in d:
            setattr(e, field, d[field])
    db.session.commit()
    return jsonify(e.to_dict())

@app.route('/api/equipes/<int:eid>', methods=['DELETE'])
def delete_equipe(eid):
    e = Equipe.query.get_or_404(eid)
    # Remove diárias vinculadas antes de deletar a equipe
    Diaria.query.filter_by(equipe_id=eid).delete()
    db.session.delete(e)
    db.session.commit()
    return jsonify({'ok': True})

# ── DIARIAS ──
@app.route('/api/diarias', methods=['GET'])
def get_diarias():
    equipe_id = request.args.get('equipe_id')
    q = Diaria.query
    if equipe_id:
        q = q.filter_by(equipe_id=int(equipe_id))
    return jsonify([d.to_dict() for d in q.order_by(Diaria.data_inicio.desc()).all()])

@app.route('/api/diarias', methods=['POST'])
def add_diaria():
    d = request.json
    qtd  = float(d.get('qtd_dias', 1))
    vdia = float(d.get('valor_dia', 0))
    total = round(qtd * vdia, 2)
    di = Diaria(
        equipe_id=int(d['equipe_id']),
        veiculo_id=int(d['veiculo_id']) if d.get('veiculo_id') else None,
        colaborador=d.get('colaborador', ''),
        data_inicio=d.get('data_inicio', ''),
        data_fim=d.get('data_fim', ''),
        qtd_dias=qtd,
        valor_dia=vdia,
        total=total,
        destino=d.get('destino', ''),
        motivo=d.get('motivo', ''),
        status=d.get('status', 'pendente')
    )
    db.session.add(di)
    db.session.commit()
    return jsonify(di.to_dict()), 201

@app.route('/api/diarias/<int:did>', methods=['PUT'])
def update_diaria(did):
    di = Diaria.query.get_or_404(did)
    d = request.json
    for field in ['equipe_id','veiculo_id','colaborador','data_inicio','data_fim','qtd_dias','valor_dia','destino','motivo','status']:
        if field in d:
            setattr(di, field, d[field])
    di.total = round((di.qtd_dias or 1) * (di.valor_dia or 0), 2)
    db.session.commit()
    return jsonify(di.to_dict())

@app.route('/api/diarias/<int:did>', methods=['DELETE'])
def delete_diaria(did):
    di = Diaria.query.get_or_404(did)
    db.session.delete(di)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/dashboard/diarias', methods=['GET'])
def dashboard_diarias():
    equipes = Equipe.query.all()
    diarias = Diaria.query.all()
    total_geral = sum(d.total or 0 for d in diarias)
    total_dias  = sum(d.qtd_dias or 0 for d in diarias)
    por_equipe = []
    for e in equipes:
        eds = [d for d in diarias if d.equipe_id == e.id]
        por_equipe.append({
            'equipe_id': e.id, 'equipe': e.nome,
            'total': round(sum(d.total or 0 for d in eds), 2),
            'qtd_dias': sum(d.qtd_dias or 0 for d in eds),
            'qtd_registros': len(eds)
        })
    por_equipe.sort(key=lambda x: x['total'], reverse=True)
    por_status = {}
    for d in diarias:
        por_status[d.status] = por_status.get(d.status, 0) + (d.total or 0)
    return jsonify({
        'total_geral': round(total_geral, 2),
        'total_dias': total_dias,
        'total_registros': len(diarias),
        'total_equipes': len(equipes),
        'por_equipe': por_equipe,
        'por_status': por_status
    })

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
