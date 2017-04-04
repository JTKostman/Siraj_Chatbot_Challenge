# python libs
import argparse

# local libs
import menu
import models
import preprocess

from keras.callbacks import ModelCheckpoint
from keras_tqdm import TQDMCallback


def set_arg_parser():
    parser = argparse.ArgumentParser(description='Process eeg data. See docs/main.txt for more info')
    parser.add_argument("-v", "--verbose", action="store_true",
                    help="output verbosity")
    parser.add_argument("-m", "--model", type=str, default='dmn00.hdf5',
                        help="Specify a specific model file")
    parser.add_argument("-c", "--challenge", type=int, choices=[1, 2], default=1,
                        help="Specify the challenge type (supporting facts) {1|2}")

    return parser

def query_model(query=None, model=None, vectorizer=None):
    queryvec = vectorizer


class StoryHandler:
    def __init__(self, dmn, vectorizer, modelfile=None):
        self.dmn = dmn
        self.vectorizer = vectorizer
        self.modelfile = 'dmn{:02}.hdf5'.format(0) if modelfile is None else modelfile

    def get_random_story(self):
        story = self.vectorizer.get_random_story()
        self.story = story
        return story

    def load_model(self, filename, verbose=False):
        self.modelfile = filename
        try:
            self.dmn.model.load_weights(filename)
            if verbose: print('<v> Loaded model: {}'.format(modelfile))
        except OSError:
            print('~'*30 + '\nWARNING!\n')
            print('No model file [{}] found! Did you train the model yet?'.format(filename))
            print('~'*30)

    def fit_model(self, epochs=1, verbose=True):
        epochs = int(epochs) # make sure this is an int, since it may be fed in as string arg
        print('Fitting {} epochs'.format(epochs))
        filepath = self.modelfile
        checkpointer = ModelCheckpoint(monitor='val_acc', filepath=filepath, verbose=1, save_best_only=False)
        inputs_train, queries_train, answers_train = self.vectorizer.vectorize_all('train')

        inputs_test, queries_test, answers_test = self.vectorizer.vectorize_all('test')
        dmn.model.fit([inputs_train, queries_train], answers_train,
                      batch_size=32,
                      epochs=epochs,
                      validation_data=([inputs_test, queries_test], answers_test),
                      verbose=0, callbacks=[checkpointer, TQDMCallback()])

    def query(self, loop=False):
        query = input('Enter a query: ')
        queryvec = ve.vectorize_query(query)
        storyvec = ve.vectorize_story(story)
        ans = dmn.query(storyvec, queryvec)
        ans_word = ve.devectorize_ans(ans)
        print('Predicted answer:\n>> {}'.format(ans_word))
        statement = 'or q to drop back to menu >>> ' if loop else ''
        reply = input('Press enter to continue {}'.format(statement))
        print('_' * 30)
        return reply

    def query_loop(self):
        while True:
            reply = self.query(loop=True)
            if reply == 'q':
                break



if __name__ == '__main__':
    parser = set_arg_parser()
    args = parser.parse_args()
    verbose = args.verbose
    if verbose: print('<v> Verbose print on')

    challenge = args.challenge
    modelfile = 'c{}'.format(challenge) + '_' + args.model
    ve = preprocess.BabiVectorizer(challenge_num=challenge)
    dmn = models.DeepMemNet(vocab_size=ve.vocab_size, story_maxlen=ve.story_maxlen, query_maxlen=ve.query_maxlen)

    handler = StoryHandler(dmn, ve, modelfile)
    handler.load_model(modelfile, verbose=verbose)

    menu_test = menu.Menu('z', 'test',
                         [['1', 'test 1', lambda: 1],
                          ['2', 'test 10', lambda: 10],
                          ['3', 'arg test 100', menu.argPrint, {'foo': 100}]]
                         )
    menu_custom_epochs = menu.Choice('f', 'Enter number of epochs', callback=handler.fit_model, userArg='epochs')

    menu_fit = menu.Menu('f', 'Fit the model',
                [['1', 'Fit Model 1 epoch', handler.fit_model],
                 ['2', 'Fit Model 10 epochs', handler.fit_model, {'epochs':10}],
                 ['3', 'Fit Model 100 epochs', handler.fit_model, {'epochs': 100}],
                 ['x', 'Test args', menu.argPrint, {'foo': 'x test args worked'}],

                 # menu_sub
                 ]
    )

    menu_main = [['1', 'Load Random Story', handler.get_random_story],
                 ['2', 'Query', handler.query],
                 ['3', 'Query (loop)', handler.query_loop],
                 # menu.UserEntry(4, 'foo', 'rando', menu.argPrint),
                 menu_custom_epochs]

    mainmenu = menu.Menu('00', '', menu_main)

    handler.get_random_story()
    while True:
        story = handler.story
        ve.format_story(story) # Display the current story
        reply = mainmenu()
        if verbose: print('<d>Menu returned: |{}| {}'.format(reply, type(reply)))
        if reply == 'q':
            break

