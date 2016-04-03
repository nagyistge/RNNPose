import numpy as np
import theano
import theano.tensor as T
from theano import shared
from helper.utils import init_weight,init_bias,get_err_fn
from helper.optimizer import RMSprop

dtype = T.config.floatX

class lstm:
   def __init__(self,rng, n_in, n_lstm, n_out, lr=0.05, batch_size=64, output_activation=theano.tensor.nnet.relu,cost_function='mse',optimizer = RMSprop):
       self.n_in = n_in
       self.n_lstm = n_lstm
       self.n_out = n_out
       self.W_xi = init_weight((self.n_in, self.n_lstm),rng=rng,name='W_xi',sample= 'glorot')
       self.W_hi = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_hi', sample='glorot')
       self.W_ci = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_ci',sample= 'glorot')
       self.b_i  = init_bias(self.n_lstm,rng=rng, sample='zero')
       self.W_xf = init_weight((self.n_in, self.n_lstm),rng=rng,name='W_xf',sample= 'glorot')
       self.W_hf = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_hf',sample= 'glorot')
       self.W_cf = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_cf', sample='glorot')
       self.b_f = init_bias(self.n_lstm, rng=rng,sample='one')
       self.W_xc = init_weight((self.n_in, self.n_lstm),rng=rng,name='W_xc', sample='glorot')
       self.W_hc = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_hc', sample='ortho')
       self.b_c = init_bias(self.n_lstm, rng=rng,sample='zero')
       self.W_xo = init_weight((self.n_in, self.n_lstm),rng=rng,name='W_xo',sample= 'glorot')
       self.W_ho = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_ho', sample='glorot')
       self.W_co = init_weight((self.n_lstm, self.n_lstm),rng=rng,name='W_co',sample= 'glorot')
       self.b_o = init_bias(self.n_lstm,rng=rng, sample='zero')
       self.W_hy = init_weight((self.n_lstm, self.n_out),rng=rng,name='W_hy',sample= 'glorot')
       self.b_y = init_bias(self.n_out,rng=rng, sample='zero')

       self.params = [self.W_xi, self.W_hi, self.W_ci, self.b_i,
                      self.W_xf, self.W_hf, self.W_cf, self.b_f,
                      self.W_xc, self.W_hc, self.b_c,  self.W_xo,
                      self.W_ho, self.W_co, self.b_o,
                      self.W_hy, self.b_y]

       def step_lstm(x_t, h_tm1, c_tm1):
           i_t = T.nnet.sigmoid(T.dot(x_t, self.W_xi) + T.dot(h_tm1, self.W_hi) + c_tm1*self.W_ci + self.b_i)
           f_t = T.nnet.sigmoid(T.dot(x_t, self.W_xf) + T.dot(h_tm1, self.W_hf) + c_tm1* self.W_cf + self.b_f)
           c_t = f_t * c_tm1 + i_t * T.tanh(T.dot(x_t, self.W_xc) + T.dot(h_tm1, self.W_hc) + self.b_c)
           o_t = T.nnet.sigmoid(T.dot(x_t, self.W_xo)+ T.dot(h_tm1, self.W_ho) + c_t*self.W_co  + self.b_o)
           h_t = o_t * T.tanh(c_t)
           y_t = T.tanh(T.dot(h_t, self.W_hy) + self.b_y)
           return [h_t, c_t, y_t]

       X = T.tensor3() # batch of sequence of vector
       Y = T.tensor3() # batch of sequence of vector
       h0 = shared(np.zeros(shape=(batch_size,self.n_lstm), dtype=dtype)) # initial hidden state
       c0 = shared(np.zeros(shape=(batch_size,self.n_lstm), dtype=dtype)) # initial cell state

       [h_vals, c_vals, y_vals], _ = theano.scan(fn=step_lstm,
                                         sequences=X.dimshuffle(1,0,2),
                                         outputs_info=[h0, c0, None])

       self.output = y_vals.dimshuffle(1,0,2)
       cost=get_err_fn(self,cost_function,Y)

       _optimizer = optimizer(
            cost,
            self.params,
            lr=lr
        )


       self.train = theano.function(inputs=[X, Y],outputs=cost,updates=_optimizer.getUpdates(),allow_input_downcast=True)
       self.predictions = theano.function(inputs = [X], outputs = y_vals.dimshuffle(1,0,2),allow_input_downcast=True)
       self.n_param=n_lstm*n_lstm*4+n_in*n_lstm*4+n_lstm*n_out+n_lstm*3
